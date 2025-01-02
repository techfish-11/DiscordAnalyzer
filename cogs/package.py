import discord
from discord.ext import commands
from discord import app_commands
import requests
import re

class PackageSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def sanitize_input(self, content: str) -> str:
        """入力からメンションや危険な文字を無効化する"""
        sanitized = re.sub(r'@', '＠', content)  # すべての@を全角に置き換え
        return sanitized

    @app_commands.command(name="package", description="npmまたはpipのパッケージを検索します")
    @app_commands.describe(package_name="検索したいパッケージ名", manager="npmまたはpipを指定")
    async def package(self, interaction: discord.Interaction, package_name: str, manager: str):
        # 入力をサニタイズ
        package_name = self.sanitize_input(package_name)

        if manager not in ["npm", "pip"]:
            await interaction.response.send_message("パッケージマネージャーは`npm`または`pip`を指定してください。")
            return

        try:
            if manager == "npm":
                result = self.search_npm_package(package_name)
            elif manager == "pip":
                result = self.search_pip_package(package_name)

            if result:
                await interaction.response.send_message(f"検索結果:\n{result}")
            else:
                await interaction.response.send_message(f"{manager}パッケージ `{package_name}` の情報は見つかりませんでした。")
        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {str(e)}")

    def search_npm_package(self, package_name: str) -> str:
        """npmパッケージを検索 (npm registry APIを使用)"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーの自動検出

            package_info = response.json()
            latest_version = package_info.get("dist-tags", {}).get("latest", "不明")
            description = package_info.get("description", "説明なし")
            homepage = package_info.get("homepage", "情報なし")
            
            return (f"**{package_name}**\n"
                    f"バージョン: {latest_version}\n"
                    f"説明: {description}\n"
                    f"URL: {homepage}")
        except requests.HTTPError as e:
            return f"npmパッケージの取得中にHTTPエラーが発生しました: {e}"
        except Exception as e:
            return f"npmパッケージの検索中にエラーが発生しました: {str(e)}"

    def search_pip_package(self, package_name: str) -> str:
        """pipパッケージを検索 (PyPI APIを使用)"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーの自動検出

            package_info = response.json()
            version = package_info.get("info", {}).get("version", "不明")
            summary = package_info.get("info", {}).get("summary", "説明なし")
            home_page = package_info.get("info", {}).get("home_page", "情報なし")

            return (f"**{package_name}**\n"
                    f"バージョン: {version}\n"
                    f"説明: {summary}\n"
                    f"URL: {home_page}")
        except requests.HTTPError as e:
            return f"pipパッケージの取得中にHTTPエラーが発生しました: {e}"
        except Exception as e:
            return f"pipパッケージの検索中にエラーが発生しました: {str(e)}"

async def setup(bot: commands.Bot):
    """Cogを非同期で追加"""
    await bot.add_cog(PackageSearch(bot))