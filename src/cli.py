"""
Command Line Interface for Signal Transceiver.
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

from src.monitor import performance_monitor


def async_cmd(f):
    """Decorator to run async functions in click commands."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@click.group()
@click.version_option(version="1.0.0", prog_name="Signal Transceiver")
def cli():
    """Signal Transceiver - 订阅服务管理工具"""
    pass


# ============ Server Commands ============

@cli.group()
def server():
    """服务器管理命令"""
    pass


@server.command("start")
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, type=int, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式(自动重载)")
@click.option("--workers", default=1, type=int, help="工作进程数")
def start_server(host: str, port: int, reload: bool, workers: int):
    """启动服务器"""
    import uvicorn

    console.print(Panel.fit(
        f"[bold green]启动 Signal Transceiver 服务[/]\n"
        f"地址: {host}:{port}\n"
        f"工作进程: {workers}\n"
        f"重载模式: {'开启' if reload else '关闭'}",
        title="服务器"
    ))

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1
    )


@server.command("health")
@click.option("--url", default="http://localhost:8000", help="服务器地址")
@async_cmd
async def check_health(url: str):
    """检查服务器健康状态"""
    import httpx

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="检查服务器状态...", total=None)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=10)
                data = response.json()

                status_color = "green" if data["status"] == "healthy" else "red"
                console.print(Panel(
                    f"[bold {status_color}]状态: {data['status']}[/]\n"
                    f"版本: {data.get('version', 'N/A')}\n"
                    f"数据库: {data.get('database', 'N/A')}",
                    title="健康检查"
                ))
        except Exception as e:
            console.print(f"[bold red]错误: {e}[/]")


# ============ Database Commands ============

@cli.group()
def db():
    """数据库管理命令"""
    pass


@db.command("init")
@async_cmd
async def init_db():
    """初始化数据库"""
    from src.config.database import init_db as do_init_db

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="初始化数据库...", total=None)
        await do_init_db()

    console.print("[bold green]✓ 数据库初始化完成[/]")


@db.command("init-permissions")
@async_cmd
async def init_permissions():
    """初始化默认权限和角色"""
    from src.config.database import async_session_maker
    from src.services.permission_service import PermissionService

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="初始化权限...", total=None)

        async with async_session_maker() as session:
            service = PermissionService(session)
            await service.init_default_permissions()
            await service.init_default_roles()
            await session.commit()

    console.print("[bold green]✓ 权限和角色初始化完成[/]")


# ============ User Commands ============

@cli.group()
def user():
    """用户管理命令"""
    pass


@user.command("create")
@click.option("--username", prompt=True, help="用户名")
@click.option("--email", prompt=True, help="邮箱")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="密码")
@click.option("--admin", is_flag=True, help="设为管理员")
@async_cmd
async def create_user(username: str, email: str, password: str, admin: bool):
    """创建用户"""
    from src.config.database import async_session_maker
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate

    async with async_session_maker() as session:
        service = AuthService(session)
        user_data = UserCreate(
            username=username,
            email=email,  # type: ignore  # Pydantic will validate this as EmailStr
            password=password
        )

        try:
            user, api_key = await service.register_user(user_data)

            if admin:
                user.is_admin = True
                await session.commit()

            console.print(Panel(
                f"[bold green]用户创建成功![/]\n\n"
                f"用户名: {user.username}\n"
                f"邮箱: {user.email}\n"
                f"管理员: {'是' if user.is_admin else '否'}\n\n"
                f"[bold yellow]API Key (仅显示一次):[/]\n{api_key}",
                title="新用户"
            ))
        except Exception as e:
            console.print(f"[bold red]错误: {e}[/]")


@user.command("list")
@click.option("--limit", default=20, type=int, help="显示数量")
@async_cmd
async def list_users(limit: int):
    """列出用户"""
    from src.config.database import async_session_maker
    from src.models.user import User
    from sqlalchemy import select

    async with async_session_maker() as session:
        result = await session.execute(select(User).limit(limit))
        users = result.scalars().all()

        table = Table(title="用户列表")
        table.add_column("ID", style="cyan")
        table.add_column("用户名", style="green")
        table.add_column("邮箱")
        table.add_column("管理员", style="yellow")
        table.add_column("状态")
        table.add_column("创建时间")

        for user in users:
            table.add_row(
                str(user.id),
                user.username,
                user.email,
                "✓" if user.is_admin else "",
                "[green]活跃[/]" if user.is_active else "[red]禁用[/]",
                user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else ""
            )

        console.print(table)


# ============ Client Commands ============

@cli.group()
def client():
    """客户端管理命令"""
    pass


@client.command("list")
@click.option("--active-only", is_flag=True, help="仅显示活跃客户端")
@async_cmd
async def list_clients(active_only: bool):
    """列出客户端（用户）"""
    from src.config.database import async_session_maker
    from src.models.user import User
    from sqlalchemy import select

    async with async_session_maker() as session:
        query = select(User)
        if active_only:
            query = query.where(User.is_active == True)

        result = await session.execute(query)
        users = result.scalars().all()

        table = Table(title="客户端列表")
        table.add_column("ID", style="cyan")
        table.add_column("用户名", style="green")
        table.add_column("Client Key")
        table.add_column("Email")
        table.add_column("状态")
        table.add_column("创建时间")

        for u in users:
            table.add_row(
                str(u.id),
                u.username,
                u.client_key[:20] + "..." if u.client_key else "N/A",
                u.email,
                "[green]活跃[/]" if u.is_active else "[red]禁用[/]",
                u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
            )

        console.print(table)


# ============ Data Commands ============

@cli.group()
def data():
    """数据管理命令"""
    pass


@data.command("stats")
@async_cmd
async def data_stats():
    """显示数据统计"""
    from src.config.database import async_session_maker
    from src.models.data import Data
    from src.models.strategy import Strategy
    from src.models.subscription import Subscription
    from sqlalchemy import select, func

    async with async_session_maker() as session:
        # Get counts
        data_count = (await session.execute(select(func.count(Data.id)))).scalar()
        strategy_count = (await session.execute(select(func.count(Strategy.id)))).scalar()
        sub_count = (await session.execute(select(func.count(Subscription.id)))).scalar()

        table = Table(title="数据统计")
        table.add_column("指标", style="cyan")
        table.add_column("数量", style="green")

        table.add_row("数据记录", str(data_count or 0))
        table.add_row("策略", str(strategy_count or 0))
        table.add_row("订阅", str(sub_count or 0))

        console.print(table)


# ============ Report Commands ============

@cli.group()
def report():
    """报告生成命令"""
    pass


@report.command("generate")
@click.option("--type", "report_type", type=click.Choice(["data", "performance"]), default="data", help="报告类型")
@click.option("--format", "output_format", type=click.Choice(["pdf", "excel"]), default="pdf", help="输出格式")
@click.option("--output", "-o", help="输出文件路径")
@async_cmd
async def generate_report(report_type: str, output_format: str, output: Optional[str]):
    """生成报告"""
    from src.report.generator import report_service
    from src.config.database import async_session_maker
    from src.models.data import Data
    from sqlalchemy import select

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "pdf" if output_format == "pdf" else "xlsx"
        output = f"reports/{report_type}_report_{timestamp}.{ext}"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description="生成报告...", total=None)

        if report_type == "data":
            async with async_session_maker() as session:
                result = await session.execute(select(Data).limit(1000))
                records = result.scalars().all()
                data_dicts = [
                    {
                        "id": r.id,
                        "type": r.type,
                        "symbol": r.symbol,
                        "execute_date": str(r.execute_date),
                        "status": r.status,
                        "created_at": str(r.created_at)
                    }
                    for r in records
                ]

            content = await report_service.generate_data_report(
                data_dicts,
                format=output_format
            )
        else:
            stats = performance_monitor.get_current_stats()
            history = performance_monitor.get_history(60)
            content = await report_service.generate_performance_report(
                stats,
                history,
                format=output_format
            )

        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'wb') as f:
            f.write(content)

    console.print(f"[bold green]✓ 报告已生成: {output}[/]")


# ============ Monitor Commands ============

@cli.group()
def monitor():
    """监控命令"""
    pass


@monitor.command("status")
def monitor_status():
    """显示系统状态"""
    from src.monitor.dashboard import system_dashboard

    data = system_dashboard.get_dashboard_data()

    # Health status
    health = data["health"]
    health_color = {
        "healthy": "green",
        "degraded": "yellow",
        "warning": "orange",
        "critical": "red"
    }.get(health["status"], "white")

    console.print(Panel(
        f"[bold {health_color}]健康状态: {health['status'].upper()}[/]\n"
        f"健康分数: {health['score']:.1f}/100\n"
        f"运行时间: {health['uptime_hours']:.1f} 小时",
        title="系统健康"
    ))

    # System resources
    sys_table = Table(title="系统资源")
    sys_table.add_column("资源", style="cyan")
    sys_table.add_column("使用率", style="green")

    system = data["system"]
    sys_table.add_row("CPU", f"{system['cpu_percent']:.1f}%")
    sys_table.add_row("内存", f"{system['memory_percent']:.1f}%")
    sys_table.add_row("磁盘", f"{system['disk_percent']:.1f}%")

    console.print(sys_table)

    # Performance metrics
    perf = data["performance"]
    perf_table = Table(title="性能指标")
    perf_table.add_column("指标", style="cyan")
    perf_table.add_column("值", style="green")

    perf_table.add_row("请求速率", f"{perf['requests_per_second']:.2f}/s")
    perf_table.add_row("平均响应时间", f"{perf['avg_response_time_ms']:.1f}ms")
    perf_table.add_row("错误率", f"{perf['error_rate']*100:.2f}%")
    perf_table.add_row("总请求数", str(perf['total_requests']))

    console.print(perf_table)

    # Warnings
    if data["warnings"]:
        console.print("\n[bold yellow]⚠ 告警:[/]")
        for w in data["warnings"]:
            console.print(f"  [{w['level']}] {w['message']}")


# ============ Main Entry ============

def main():
    """Main entry point."""
    try:
        # Ensure we can import dependencies
        cli()
    except ImportError as e:
        console.print(f"[bold red]缺少依赖: {e}[/]")
        console.print("请运行: pip install rich click")
        sys.exit(1)


if __name__ == "__main__":
    main()
