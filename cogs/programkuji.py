import random

import discord
from discord.ext import commands


class ProgramKuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="programgacha", description="ランダムなプログラミング言語を選びます。")
    async def program_kuji(self, ctx: discord.Interaction) -> None:
        languages = [
            "Python", "JavaScript", "Java", "C#", "C++", "Ruby", "Go", "Swift", "Kotlin", "Rust",
            "Cow", "Assembly",  # 標準的な言語
            "Whitespace",  # 空白文字のみで構成された言語
            "LOLCode",  # LOLspeak（インターネットスラング）を使用した言語
            "INTERCAL",  # 意図的に不便な設計を持つジョーク言語
            "Brainf**k",  # 複雑なシンタックスで有名な言語
            "Malbolge",  # 最も難解なプログラミング言語の一つ
            "Befunge",  # 二次元コードを使った逆転的な言語
            "Piet",  # アートのようなプログラムを書く言語
            "ArnoldC",  # アーノルド・シュワルツェネッガーのセリフを使う言語
            "Chef",  # 料理レシピのようなコード
            "Shakespeare",  # シェイクスピア風の言語
            "Dog",  # 犬をテーマにした言語
            "Unlambda",  # 非常に抽象的な言語
            "Ook!",  # 猿の言語を模倣したプログラミング言語
            "LOLCats",  # 猫の言語 (LOLCodeの猫バージョン)
            "Whitespace",  # 空白文字だけでプログラムを書く言語
            "Chicken",  # すべて「Chicken」で構成される言語
            "MOO",  # ただしコードがとても直感的なMOO言語
            "Tiny BASIC",  # 超小型なBASIC
            "Haskell-92",  # 普通のHaskellではなくバージョン92
            "COW",  # "Moo"を使う言語、非常に限定的な命令で動作
            "PicoLisp",  # シンプルなLisp派生言語、だが使いづらい
            "Bash"  # シェルスクリプトだけど普通に使われてる
            "GOTO",  # ラベル制御を多用する非常に混乱するような言語
            "Spaghetti",  # スパゲッティコードを書くための言語
            "Forth",  # ユニークなスタックベースの命令型言語（でも意外と使える）
            "Hack",  # もはやジョークじゃないけど、語呂が面白い名前
            "PHP",  # プログラマにはジョークとして知られるが、実際には使われる言語
            "JScript",  # JavaScriptのジョークバージョン
            "Xojo",  # 宣伝してる割に使いづらい言語
            "Zig",  # 複雑な設定が要されるC系言語、ジョークみたいな動作もあり
            "PICO",  # PICOがコードの中に出てきます
            "Dancing",  # プログラムでダンスを表現するジョーク言語
            "Yorick",  # なんでもできると言いながら難解な構文
            "ZPL",  # 宣伝文の割に難解なマイナー言語
            "Monkey",  # サルが操作するような簡単すぎる命令の言語
            "FORTRAN",  # 昔の言語がジョークにされがち
            "Babel",  # プログラム中に言語をバラバラにさせてしまう言語
            "Markov",  # 高度にランダムでコンパイルされないことを狙った言語
            "ClojureScript",  # Clojureがジョークにされている編成
            "ZPL"  # 古典的な構文ルールの変形を誇りにする言語
        ]

        chosen_language = random.choice(languages)

        embed = discord.Embed(
            title="プログラミング言語ガチャ", description=f"ガチャで出てきたプログラミング言語は: {chosen_language} です！", color=discord.Color.blue())

        await ctx.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ProgramKuji(bot))
