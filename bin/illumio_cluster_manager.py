#!/usr/bin/env python3
import click
import asyncio
from typing import Optional
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Settings, VaultConfig
from app.core.api_client import BaseAPIClient
from app.core.vault_client import VaultClient
from app.bin.illumio import ejvault
from app.services import IllumioService, KubernetesService
from app.utils import get_logger, KubernetesError
from app.utils.exceptions import IllumioError
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from functools import wraps

console = Console()

def coro(f):
    """Decorator to run async functions."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.group()
@click.option('--verbose', is_flag=True, help='Enable debug logging')
@click.option('--dry-run', is_flag=True, help='Simulate actions without making changes')
@click.option('--config', type=str, help='Path to config file')
@click.pass_context
def cli(ctx, verbose: bool, dry_run: bool, config: Optional[str]):
    """Illumio Kubernetes Cluster Manager CLI"""
    ctx.ensure_object(dict)
    
    try:
        # Initialize settings
        settings = Settings(_env_file=config) if config else Settings()
        vault_config = VaultConfig(_env_file=config) if config else VaultConfig()
        
        # Configure logging
        logger = get_logger(__name__, level="DEBUG" if verbose else "INFO")
        
        # Initialize services
        _, api_user, api_key = ejvault.get_pce_secrets()
        settings.api_key = api_key
        settings.api_user = api_user
        api_client = BaseAPIClient(settings)
        vault_client = VaultClient(vault_config)
        k8s_service = KubernetesService()
        illumio_service = IllumioService(api_client, vault_client)
        

        ctx.obj.update({
            'settings': settings,
            'vault_config': vault_config,
            'logger': logger,
            'illumio': illumio_service,
            'k8s': k8s_service,
            'dry_run': dry_run
        })
        
    except Exception as e:
        console.print(f"[red]Configuration error:[/red] {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('cluster-name')
@click.option('--namespace', default='illumio-system', help='Kubernetes namespace')
@click.option('--enforce/--no-enforce', default=False, help='Enable enforcement mode')
@click.pass_context
@coro
async def create_cluster(ctx, cluster_name: str, namespace: str, enforce: bool):
    """Create and configure a new Illumio cluster."""
    illumio, k8s = ctx.obj['illumio'], ctx.obj['k8s']
    logger = ctx.obj['logger']
    dry_run = ctx.obj['dry_run']
    
    try:
        with console.status("[bold green]Creating cluster...") as status:
            # Check if cluster exists
            existing = await illumio.get_cluster(cluster_name)
            if existing:
                console.print(f"[yellow]Cluster {cluster_name} already exists[/yellow]")
                return
            
            if not dry_run:
                # Create cluster in Illumio
                status.update("[bold green]Creating Illumio cluster configuration...")
                cluster = await illumio.create_cluster(
                    cluster_name,
                    description=f"Managed cluster: {cluster_name}",
                    enforcement_mode="enforce" if enforce else "visibility_only"
                )
                
                # Create Kubernetes namespace - Commented out as requested
                # status.update("[bold green]Creating Kubernetes namespace...")
                # await k8s.create_namespace(namespace)
                
                # Create workload profile
                status.update("[bold green]Creating workload profile...")
                await illumio.create_namespace_profile(
                    cluster.href.split('/')[-1],
                    namespace
                )
                
                console.print("[green]✓[/green] Cluster setup completed successfully")
                
    except (IllumioError, KubernetesError) as e:
        logger.error(f"Cluster creation failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('cluster-name')
@click.pass_context
@coro
async def delete_cluster(ctx, cluster_name: str):
    """Delete an Illumio cluster and associated resources."""
    illumio, k8s = ctx.obj['illumio'], ctx.obj['k8s']
    logger = ctx.obj['logger']
    dry_run = ctx.obj['dry_run']
    
    try:
        if not dry_run:
            # Delete cluster
            if await illumio.delete_cluster(cluster_name):
                console.print(f"[green]✓[/green] Cluster {cluster_name} deleted successfully")
            else:
                console.print(f"[yellow]Cluster {cluster_name} not found[/yellow]")
                
    except (IllumioError, KubernetesError) as e:
        logger.error(f"Cluster deletion failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.pass_context
@coro
async def list_clusters(ctx):
    """List all Illumio clusters."""
    illumio = ctx.obj['illumio']
    logger = ctx.obj['logger']
    
    try:
        clusters = await illumio.list_clusters()
        
        if not clusters:
            console.print("[yellow]No clusters found[/yellow]")
            return
            
        # Create table
        table = Table(title="Illumio Clusters")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Enforcement", style="yellow")
        table.add_column("Created", style="blue")
        
        for cluster in clusters:
            table.add_row(
                cluster.name,
                "Active" if cluster.online else "Offline",
                cluster.enforcement_mode,
                cluster.created_at.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        console.print(table)
        
    except IllumioError as e:
        logger.error(f"Failed to list clusters: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('cluster-name')
@click.pass_context
@coro
async def get_cluster(ctx, cluster_name: str):
    """Get detailed information about a cluster."""
    illumio = ctx.obj['illumio']
    logger = ctx.obj['logger']
    
    try:
        cluster = await illumio.get_cluster(cluster_name)
        if not cluster:
            console.print(f"[yellow]Cluster {cluster_name} not found[/yellow]")
            return
            
        # Display cluster details
        rprint({
            "name": cluster.name,
            "status": "Active" if cluster.online else "Offline",
            "enforcement_mode": cluster.enforcement_mode,
            "created_at": cluster.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": cluster.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "labels": cluster.labels,
            "container_cluster_token": "***" if cluster.container_cluster_token else None
        })
        
    except IllumioError as e:
        logger.error(f"Failed to get cluster details: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()