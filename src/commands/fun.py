import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import re
from datetime import datetime, timezone
from utils.helpers import create_success_embed, create_error_embed

# Data for fun commands
COMPLIMENTS = [
    "You're coding like a pro! 🚀",
    "Your problem-solving skills are impressive! 🧠",
    "You're crushing it today! 💪",
    "You make debugging look easy! 🔍",
    "Your code is cleaner than my cache! ✨",
    "You're the exception to null pointer errors! ⭐",
    "You're the semicolon to my statement! 😊",
]

DAD_JOKES = [
    "Why don't programmers like nature? It has too many bugs!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why don't skeletons fight each other? They don't have the guts!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
]

FORTUNE_COOKIES = [
    "A beautiful, smart, and loving person will be coming into your code base.",
    "Your commit will bring you good luck.",
    "Now is the time to try something new with your code.",
    "The bug you're looking for is in another file.",
    "You will soon be the center of a git merge conflict.",
    "Your code will compile on the first try today.",
    "A mysterious pull request will bring unexpected joy.",
    "Don't worry about the bugs of tomorrow, deal with the exceptions of today.",
]

WOULD_YOU_RATHER = [
    {"option1": "Only be able to write Python", "option2": "Only be able to write JavaScript"},
    {"option1": "Have perfect code but no comments", "option2": "Buggy code with perfect documentation"},
    {"option1": "Be able to predict all runtime errors", "option2": "Be able to predict all compilation errors"},
    {"option1": "Always have to code in light mode", "option2": "Always have to code without auto-complete"},
    {"option1": "Write code that no one can understand but works perfectly", "option2": "Write code everyone understands but takes twice as long to run"},
]

HANGMAN_WORDS = [
    "python", "javascript", "programming", "database", "algorithm",
    "function", "variable", "debugging", "framework", "developer",
    "compiler", "frontend", "backend", "fullstack", "docker",
    "github", "linux", "server", "cloud", "agile"
]

PROGRAMMING_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the programmer quit his job? Because he didn't get arrays!",
    "What's a programmer's favorite hangout spot? The Foo Bar!",
    "Why do programmers always mix up Christmas and Halloween? Because Oct 31 == Dec 25!",
    "Why do Java developers wear glasses? Because they don't C#",
    "Why did the developer go broke? Because he used up all his cache!",
    "What do you call a programmer from Finland? Nerdic!",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself!",
    "What's a pirate's favorite programming language? R!",
    "Why do programmers hate nature? It has too many bugs!",
    "What's a programmer's favorite place in New York? Boolean Manhattan!",
]

RIDDLES = [
    {"question": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "answer": "an echo"},
    {"question": "What has keys, but no locks; space, but no room; and you can enter, but not go in?", "answer": "a keyboard"},
    {"question": "What gets bigger when more is taken away?", "answer": "a hole"},
    {"question": "I am taken from a mine and shut up in a wooden case, from which I am never released, and yet I am used by everyone. What am I?", "answer": "a pencil lead"},
    {"question": "What kind of tree can you carry in your hand?", "answer": "a palm"},
    {"question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. I have roads, but no cars. What am I?", "answer": "a map"},
    {"question": "The more you code, the more of me there is. I may be gone for now but you can't get rid of me forever. What am I?", "answer": "a bug"},
]

TRIVIA_QUESTIONS = [
    {
        "question": "What does API stand for?",
        "options": [
            "Application Programming Interface",
            "Advanced Programming Interface", 
            "Automated Programming Interface",
            "Application Protocol Interface"
        ],
        "answer": "Application Programming Interface",
        "category": "basics"
    },
    {
        "question": "Which data structure uses LIFO?",
        "options": ["Queue", "Stack", "Tree", "Linked List"],
        "answer": "Stack",
        "category": "data_structures"
    },
    {
        "question": "What is the time complexity of binary search?",
        "options": ["O(n)", "O(log n)", "O(n²)", "O(n log n)"],
        "answer": "O(log n)",
        "category": "algorithms"
    }
]

# Code snippet templates for different languages
CODE_SNIPPETS = {
    "python": {
        "quicksort": """```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```""",
        "binary_search": """```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```""",
        "fibonacci": """```python
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```""",
        "api_request": """```python
import requests

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None
```""",
        "file_operations": """```python
# Read file
with open('file.txt', 'r') as f:
    content = f.read()

# Write file
with open('file.txt', 'w') as f:
    f.write('Hello, World!')

# Append to file
with open('file.txt', 'a') as f:
    f.write('New line\\n')
```"""
    },
    "javascript": {
        "quicksort": """```javascript
function quicksort(arr) {
    if (arr.length <= 1) return arr;
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    return [...quicksort(left), ...middle, ...quicksort(right)];
}
```""",
        "fetch_api": """```javascript
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}
```""",
        "debounce": """```javascript
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}
```""",
        "deep_clone": """```javascript
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    const cloned = {};
    for (let key in obj) {
        if (obj.hasOwnProperty(key)) {
            cloned[key] = deepClone(obj[key]);
        }
    }
    return cloned;
}
```"""
    },
    "java": {
        "quicksort": """```java
public static void quicksort(int[] arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

private static int partition(int[] arr, int low, int high) {
    int pivot = arr[high];
    int i = (low - 1);
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            int temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }
    int temp = arr[i + 1];
    arr[i + 1] = arr[high];
    arr[high] = temp;
    return i + 1;
}
```""",
        "singleton": """```java
public class Singleton {
    private static volatile Singleton instance;
    
    private Singleton() {}
    
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```"""
    },
    "cpp": {
        "binary_search": """```cpp
#include <vector>

int binarySearch(std::vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```""",
        "linked_list": """```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

class LinkedList {
public:
    ListNode* head;
    
    LinkedList() : head(nullptr) {}
    
    void insert(int val) {
        ListNode* newNode = new ListNode(val);
        newNode->next = head;
        head = newNode;
    }
    
    void display() {
        ListNode* temp = head;
        while (temp) {
            std::cout << temp->val << " ";
            temp = temp->next;
        }
    }
};
```"""
    }
}

# Regular expressions for common patterns
REGEX_PATTERNS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone": r"^(\+\d{1,3}[- ]?)?\d{10}$",
    "url": r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
    "ip": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    "hex_color": r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
    "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$",
    "password": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
}

# Big O complexity explanations
BIG_O_COMPLEXITIES = {
    "O(1)": "**Constant Time** - Always takes the same time regardless of input size. Example: Array access by index.",
    "O(log n)": "**Logarithmic Time** - Efficient for large datasets. Example: Binary search in sorted array.",
    "O(n)": "**Linear Time** - Time increases linearly with input size. Example: Finding an item in unsorted array.",
    "O(n log n)": "**Linearithmic Time** - Common in efficient sorting algorithms. Example: Merge sort, Quick sort.",
    "O(n²)": "**Quadratic Time** - Time increases quadratically. Example: Bubble sort, nested loops.",
    "O(n³)": "**Cubic Time** - Very slow for large inputs. Example: Naive matrix multiplication.",
    "O(2^n)": "**Exponential Time** - Extremely slow, avoid for large inputs. Example: Naive Fibonacci recursion.",
    "O(n!)": "**Factorial Time** - Extremely slow, only viable for very small inputs. Example: Traveling salesman brute force."
}

# HTTP status codes
HTTP_STATUS_CODES = {
    200: "OK - Request successful",
    201: "Created - Resource created successfully",
    204: "No Content - Request successful, no content to return",
    400: "Bad Request - Invalid request syntax",
    401: "Unauthorized - Authentication required",
    403: "Forbidden - Access denied",
    404: "Not Found - Resource not found",
    405: "Method Not Allowed - HTTP method not supported",
    409: "Conflict - Request conflicts with current state",
    429: "Too Many Requests - Rate limit exceeded",
    500: "Internal Server Error - Server error",
    502: "Bad Gateway - Invalid response from upstream server",
    503: "Service Unavailable - Server temporarily unavailable"
}

# Common Git commands
GIT_COMMANDS = {
    "init": "git init - Initialize a new Git repository",
    "clone": "git clone <url> - Clone a repository from remote",
    "add": "git add <file> - Stage changes for commit",
    "commit": "git commit -m 'message' - Commit staged changes",
    "push": "git push origin <branch> - Push commits to remote",
    "pull": "git pull origin <branch> - Pull changes from remote",
    "status": "git status - Check repository status",
    "log": "git log --oneline - View commit history",
    "branch": "git branch <name> - Create new branch",
    "checkout": "git checkout <branch> - Switch to branch",
    "merge": "git merge <branch> - Merge branch into current",
    "reset": "git reset --hard <commit> - Reset to specific commit",
    "stash": "git stash - Temporarily save changes",
    "rebase": "git rebase <branch> - Reapply commits on top of another branch"
}

class Fun(commands.Cog):
    """Fun commands for entertainment and engagement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.hangman_games = {}

    @commands.hybrid_command(name="compliment", help="Get a random compliment")
    async def compliment(self, ctx, member: discord.Member = None):
        """Send a random compliment to yourself or another member"""
        target = member or ctx.author
        compliment = random.choice(COMPLIMENTS)
        embed = discord.Embed(
            title="💝 Compliment!",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dadjoke", help="Get a random dad joke")
    async def dadjoke(self, ctx):
        """Get a random dad joke"""
        joke = random.choice(DAD_JOKES)
        embed = discord.Embed(
            title="👨 Dad Joke!",
            description=joke,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="fortune", help="Get your programming fortune")
    async def fortune(self, ctx):
        """Get a programming-themed fortune cookie message"""
        fortune = random.choice(FORTUNE_COOKIES)
        embed = discord.Embed(
            title="🥠 Your Programming Fortune",
            description=fortune,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="wyr", help="Would you rather...? (cooldown 30s per channel)")
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def would_you_rather(self, ctx):
        """Start a would you rather game"""
        question = random.choice(WOULD_YOU_RATHER)
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            color=discord.Color.blue()
        )
        embed.add_field(name="1️⃣", value=question["option1"], inline=False)
        embed.add_field(name="2️⃣", value=question["option2"], inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")

    @commands.hybrid_command(name="hangman", help="Play hangman with programming words")
    async def hangman(self, ctx):
        """Start a game of hangman"""
        if ctx.channel.id in self.hangman_games:
            await ctx.send("A game is already in progress in this channel!")
            return

        word = random.choice(HANGMAN_WORDS).upper()
        guessed = set()
        tries = 6
        
        self.hangman_games[ctx.channel.id] = {
            "word": word,
            "guessed": guessed,
            "tries": tries
        }

        def get_display_word():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        embed = discord.Embed(
            title="🎯 Hangman - Programming Edition",
            description=f"```\n{get_display_word()}\n```\nTries left: {tries}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="joke", help="Get a random programming joke")
    async def joke(self, ctx):
        """Get a random programming joke"""
        joke = random.choice(PROGRAMMING_JOKES)
        embed = discord.Embed(
            title="😄 Programming Joke",
            description=joke,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="flip", help="Flip a coin")
    async def flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on: **{result}**!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="8ball", help="Ask the magic 8-ball a question")
    @app_commands.describe(question="The question you want to ask the magic 8-ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        responses = [
            "It is certain", "Without a doubt", "Yes definitely",
            "You may rely on it", "As I see it, yes", "Most likely",
            "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy, try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.purple(), timestamp=datetime.now(tz=timezone.utc))
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="riddle", help="Get a random riddle to solve")
    async def riddle(self, ctx):
        """Start a riddle game"""
        riddle = random.choice(RIDDLES)
        embed = discord.Embed(
            title="🤔 Riddle Time!",
            description=riddle["question"],
            color=discord.Color.purple()
        )
        embed.set_footer(text="Reply with your answer within 30 seconds!")
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if guess.content.lower() == riddle["answer"]:
                await ctx.send(f"🎉 Correct, {ctx.author.mention}! Well done!")
            else:
                await ctx.send(f"❌ Sorry, that's not correct. The answer was: {riddle['answer']}")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! Better luck next time!")

    @commands.hybrid_command(name="trivia", help="Start a trivia question")
    async def trivia(self, ctx):
        """Start a trivia game"""
        question = random.choice(TRIVIA_QUESTIONS)
        options = question["options"]
        random.shuffle(options)

        embed = discord.Embed(
            title="🎯 Programming Trivia",
            description=question["question"],
            color=discord.Color.gold()
        )
        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=True)
        embed.set_footer(text="Reply with the number of your answer (1-4) within 30 seconds!")
        
        await ctx.send(embed=embed)

        def check(m):
            return (m.author == ctx.author and 
                   m.channel == ctx.channel and 
                   m.content.isdigit() and 
                   1 <= int(m.content) <= 4)

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if options[int(guess.content)-1] == question["answer"]:
                await ctx.send(f"✨ Correct, {ctx.author.mention}! You're a genius!")
            else:
                await ctx.send(f"❌ Not quite! The correct answer was: {question['answer']}")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! The answer was: " + question["answer"])

    @commands.hybrid_command(name="rps", help="Play Rock, Paper, Scissors: ?rps <rock|paper|scissors>")
    async def rps(self, ctx, choice: str):
        """Play Rock, Paper, Scissors"""
        choice = choice.lower()
        choices = ["rock", "paper", "scissors"]
        
        if choice not in choices:
            await ctx.send("Please choose either rock, paper, or scissors!")
            return

        bot_choice = random.choice(choices)
        
        embed = discord.Embed(title="🎮 Rock, Paper, Scissors!", color=discord.Color.blue())
        embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
        embed.add_field(name="Bot's Choice", value=bot_choice.capitalize(), inline=True)
        
        if choice == bot_choice:
            result = "It's a tie! 🤝"
        elif ((choice == "rock" and bot_choice == "scissors") or 
              (choice == "paper" and bot_choice == "rock") or 
              (choice == "scissors" and bot_choice == "paper")):
            result = f"You win! 🎉"
        else:
            result = "Bot wins! 🤖"
        
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roll", help="Roll dice in NdN format, e.g. 2d6")
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format"""
        try:
            match = re.match(r"(\d+)d(\d+)", dice)
            if not match:
                await ctx.send("Format must be NdN (e.g., 2d6 for two six-sided dice)")
                return

            number, sides = map(int, match.groups())
            if number > 100:
                await ctx.send("Cannot roll more than 100 dice at once!")
                return
            if sides > 100:
                await ctx.send("Cannot roll dice with more than 100 sides!")
                return

            rolls = [random.randint(1, sides) for _ in range(number)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Rolling {dice}...",
                color=discord.Color.green()
            )
            embed.add_field(name="Rolls", value=", ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

    @commands.hybrid_command(name="kill", help="Playfully 'kill' another user with a funny method")
    async def kill(self, ctx, user: discord.Member):
        """Playfully 'kill' another user with a random funny method"""
        # Prevent self-targeting
        if user.id == ctx.author.id:
            embed = discord.Embed(
                title="⚠️ Self-Preservation Mode",
                description="You cannot kill yourself! That's not how this works!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        # Prevent targeting the bot
        if user.bot:
            embed = discord.Embed(
                title="🤖 Bot Protection",
                description="Nice try, but bots are immortal! 🛡️",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        kill_methods = [
            "brutally defeated with a keyboard",
            "eliminated with a logic bomb",
            "destroyed by an infinite loop",
            "terminated with a stack overflow",
            "annihilated by a null pointer exception",
            "obliterated with a segmentation fault",
            "vaporized by a memory leak",
            "executed via system call",
            "deleted from existence",
            "crashed by a buffer overflow",
            "eliminated with extreme prejudice",
            "sent to the shadow realm",
            "banished to /dev/null",
            "compressed into a .zip file",
            "converted to binary and forgotten",
            "recursively deleted",
            "force-quit from life",
            "ctrl+alt+deleted from reality",
            "blue-screened permanently",
            "kernel panicked out of existence",
            "garbage collected permanently",
            "deadlocked in an eternal sleep",
            "hit by a massive data breach",
            "consumed by a black hole algorithm",
            "suffocated by spaghetti code"
        ]

        method = random.choice(kill_methods)
        
        embed = discord.Embed(
            title="☠️ Elimination Complete",
            description=f"**{ctx.author.display_name}** has {method} **{user.display_name}**!",
            color=discord.Color.red()
        )
        embed.set_footer(text="This is just for fun! No actual harm intended 😄")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="hangman", help="Play hangman with programming words")
    async def hangman(self, ctx):
        """Start a game of hangman"""
        if ctx.channel.id in self.hangman_games:
            await ctx.send("A game is already in progress in this channel!")
            return

        word = random.choice(HANGMAN_WORDS).upper()
        guessed = set()
        tries = 6
        
        self.hangman_games[ctx.channel.id] = {
            "word": word,
            "guessed": guessed,
            "tries": tries
        }

        def get_display_word():
            return " ".join(letter if letter in guessed else "_" for letter in word)

        embed = discord.Embed(
            title="🎯 Hangman - Programming Edition",
            description=f"```\n{get_display_word()}\n```\nTries left: {tries}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="poll", help="Create a poll: ?poll <question> | <opt1> | <opt2> [| opt3 | opt4]")
    async def poll(self, ctx: commands.Context, *, spec: str):
        parts = [p.strip() for p in spec.split('|') if p.strip()]
        if len(parts) < 3:
            await ctx.send("Format: ?poll Question text | Option 1 | Option 2 [| Option 3 | Option 4]")
            return
        question, *options = parts
        if len(options) > 4:
            options = options[:4]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue(), timestamp=datetime.now(tz=timezone.utc))
        for i, option in enumerate(options):
            embed.add_field(name=f"{emojis[i]} Option {i+1}", value=option, inline=False)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        message = await ctx.send(embed=embed)
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
    
    @commands.command(name="guess", help="Start a number guessing game: ?guess [max_number]")
    async def guess_game(self, ctx: commands.Context, max_number: int = 100):
        """Number guessing game"""
        if max_number < 2 or max_number > 1000:
            await ctx.send("❌ Please choose a number between 2 and 1000!")
            return
        
        number = random.randint(1, max_number)
        attempts = 0
        max_attempts = min(10, max(3, max_number // 10))
        embed = discord.Embed(title="🎯 Number Guessing Game", description=f"I'm thinking of a number between 1 and {max_number}!\nYou have {max_attempts} attempts.", color=discord.Color.green())
        await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while attempts < max_attempts:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                attempts += 1
                
                try:
                    guess = int(msg.content)
                except ValueError:
                    await msg.reply("Please enter a valid number!")
                    continue
                
                if guess == number:
                    await msg.reply(f"🎉 Congratulations! You guessed it in {attempts} attempts! The number was {number}.")
                    return
                elif guess < number:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📈 Too low! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📈 Too low! Game over! The number was {number}.")
                else:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📉 Too high! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📉 Too high! Game over! The number was {number}.")
                        
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The number was {number}.")
                return

        await ctx.send(f"💔 Game over! The number was {number}. Better luck next time!")
    
    @commands.command(name="poll", help="Create a poll: ?poll <question> | <opt1> | <opt2> [| opt3 | opt4]")
    async def poll(self, ctx: commands.Context, *, spec: str):
        parts = [p.strip() for p in spec.split('|') if p.strip()]
        if len(parts) < 3:
            await ctx.send("Format: ?poll Question text | Option 1 | Option 2 [| Option 3 | Option 4]")
            return
        question, *options = parts
        if len(options) > 4:
            options = options[:4]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue(), timestamp=datetime.now(tz=timezone.utc))
        for i, option in enumerate(options):
            embed.add_field(name=f"{emojis[i]} Option {i+1}", value=option, inline=False)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        message = await ctx.send(embed=embed)
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
    
    @commands.command(name="guess", help="Start a number guessing game: ?guess [max_number]")
    async def guess_game(self, ctx: commands.Context, max_number: int = 100):
        """Number guessing game"""
        if max_number < 2 or max_number > 1000:
            await ctx.send("❌ Please choose a number between 2 and 1000!")
            return
        
        number = random.randint(1, max_number)
        attempts = 0
        max_attempts = min(10, max(3, max_number // 10))
        embed = discord.Embed(title="🎯 Number Guessing Game", description=f"I'm thinking of a number between 1 and {max_number}!\nYou have {max_attempts} attempts.", color=discord.Color.green())
        await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while attempts < max_attempts:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                attempts += 1
                
                try:
                    guess = int(msg.content)
                except ValueError:
                    await msg.reply("Please enter a valid number!")
                    continue
                
                if guess == number:
                    await msg.reply(f"🎉 Congratulations! You guessed it in {attempts} attempts! The number was {number}.")
                    return
                elif guess < number:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📈 Too low! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📈 Too low! Game over! The number was {number}.")
                else:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📉 Too high! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📉 Too high! Game over! The number was {number}.")
                        
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The number was {number}.")
                return

        await ctx.send(f"💔 Game over! The number was {number}. Better luck next time!")

    @commands.hybrid_command(name="snippet", help="Get code snippets for common algorithms")
    @app_commands.describe(
        language="Programming language (python, javascript, java, cpp)",
        algorithm="Algorithm name (quicksort, binary_search, fibonacci, etc.)"
    )
    async def snippet(self, ctx: commands.Context, language: str, algorithm: str):
        """Get code snippets for common algorithms and patterns"""
        language = language.lower()
        algorithm = algorithm.lower()
        
        if language not in CODE_SNIPPETS:
            available_langs = ", ".join(CODE_SNIPPETS.keys())
            await ctx.send(f"❌ Language not found. Available: {available_langs}")
            return
        
        if algorithm not in CODE_SNIPPETS[language]:
            available_algos = ", ".join(CODE_SNIPPETS[language].keys())
            await ctx.send(f"❌ Algorithm not found for {language}. Available: {available_algos}")
            return
        
        embed = discord.Embed(
            title=f"📄 {algorithm.replace('_', ' ').title()} - {language.title()}",
            description=CODE_SNIPPETS[language][algorithm],
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Use ?snippet {language} <algorithm> for more snippets")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="regex", help="Get common regex patterns")
    @app_commands.describe(pattern="Pattern type (email, phone, url, ip, etc.)")
    async def regex(self, ctx: commands.Context, pattern: str = None):
        """Get common regex patterns for validation"""
        if pattern is None:
            patterns_list = ", ".join(REGEX_PATTERNS.keys())
            embed = discord.Embed(
                title="🔍 Available Regex Patterns",
                description=f"**Available patterns:** {patterns_list}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Usage", 
                value="Use `?regex <pattern>` to get a specific pattern",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        pattern = pattern.lower()
        if pattern not in REGEX_PATTERNS:
            patterns_list = ", ".join(REGEX_PATTERNS.keys())
            await ctx.send(f"❌ Pattern not found. Available: {patterns_list}")
            return
        
        embed = discord.Embed(
            title=f"🔍 Regex Pattern: {pattern.title()}",
            description=f"```regex\n{REGEX_PATTERNS[pattern]}\n```",
            color=discord.Color.green()
        )
        
        # Add examples for specific patterns
        examples = {
            "email": "john.doe@example.com",
            "phone": "+1 555-123-4567",
            "url": "https://www.example.com/path?query=value",
            "ip": "192.168.1.1",
            "hex_color": "#FF5733 or #F53",
            "password": "Must have: uppercase, lowercase, digit, special char, 8+ length"
        }
        
        if pattern in examples:
            embed.add_field(name="Example", value=examples[pattern], inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bigO", help="Explain Big O complexity notation")
    @app_commands.describe(complexity="Complexity notation (O(1), O(n), O(log n), etc.)")
    async def big_o(self, ctx: commands.Context, complexity: str = None):
        """Explain Big O complexity notation"""
        if complexity is None:
            complexities_list = ", ".join(BIG_O_COMPLEXITIES.keys())
            embed = discord.Embed(
                title="📊 Big O Complexity Guide",
                description=f"**Available complexities:** {complexities_list}",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Usage", 
                value="Use `?bigO <complexity>` for detailed explanation",
                inline=False
            )
            embed.add_field(
                name="Order (Best to Worst)",
                value="O(1) → O(log n) → O(n) → O(n log n) → O(n²) → O(n³) → O(2^n) → O(n!)",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        complexity = complexity.upper().replace(" ", "")
        if complexity not in BIG_O_COMPLEXITIES:
            complexities_list = ", ".join(BIG_O_COMPLEXITIES.keys())
            await ctx.send(f"❌ Complexity not found. Available: {complexities_list}")
            return
        
        embed = discord.Embed(
            title=f"📊 Big O Notation: {complexity}",
            description=BIG_O_COMPLEXITIES[complexity],
            color=discord.Color.purple()
        )
        
        # Add visual representation for some complexities
        if complexity == "O(1)":
            embed.add_field(name="Graph", value="```\nTime |\n     |●●●●●●●●●●●\n     |___________\n          Input Size```", inline=False)
        elif complexity == "O(N)":
            embed.add_field(name="Graph", value="```\nTime |      ●\n     |    ●\n     |  ●\n     |●\n     |___________\n          Input Size```", inline=False)
        elif complexity == "O(N²)":
            embed.add_field(name="Graph", value="```\nTime |         ●\n     |      ●\n     |   ●\n     | ●\n     |●\n     |___________\n          Input Size```", inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="http", help="Look up HTTP status codes")
    @app_commands.describe(code="HTTP status code (200, 404, 500, etc.)")
    async def http_status(self, ctx: commands.Context, code: int = None):
        """Look up HTTP status codes"""
        if code is None:
            embed = discord.Embed(
                title="🌐 Common HTTP Status Codes",
                color=discord.Color.blue()
            )
            embed.add_field(name="2xx Success", value="200, 201, 204", inline=True)
            embed.add_field(name="4xx Client Error", value="400, 401, 403, 404, 429", inline=True)
            embed.add_field(name="5xx Server Error", value="500, 502, 503", inline=True)
            embed.add_field(
                name="Usage", 
                value="Use `?http <code>` for specific status code info",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        if code not in HTTP_STATUS_CODES:
            await ctx.send(f"❌ HTTP status code {code} not found in common codes.")
            return
        
        embed = discord.Embed(
            title=f"🌐 HTTP Status Code: {code}",
            description=HTTP_STATUS_CODES[code],
            color=discord.Color.blue()
        )
        
        # Color coding based on status type
        if 200 <= code < 300:
            embed.color = discord.Color.green()
        elif 400 <= code < 500:
            embed.color = discord.Color.orange()
        elif 500 <= code < 600:
            embed.color = discord.Color.red()
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="git", help="Get common Git commands and explanations")
    @app_commands.describe(command="Git command (init, clone, add, commit, etc.)")
    async def git_help(self, ctx: commands.Context, command: str = None):
        """Get Git command explanations and usage"""
        if command is None:
            embed = discord.Embed(
                title="📚 Git Commands Reference",
                color=discord.Color.gold()
            )
            
            basic_commands = ["init", "clone", "add", "commit", "push", "pull"]
            advanced_commands = ["branch", "merge", "rebase", "stash", "reset", "log"]
            
            embed.add_field(
                name="Basic Commands", 
                value=", ".join(basic_commands), 
                inline=False
            )
            embed.add_field(
                name="Advanced Commands", 
                value=", ".join(advanced_commands), 
                inline=False
            )
            embed.add_field(
                name="Usage", 
                value="Use `?git <command>` for specific command info",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        command = command.lower()
        if command not in GIT_COMMANDS:
            available_commands = ", ".join(GIT_COMMANDS.keys())
            await ctx.send(f"❌ Git command not found. Available: {available_commands}")
            return
        
        embed = discord.Embed(
            title=f"📚 Git Command: {command}",
            description=f"```bash\n{GIT_COMMANDS[command]}\n```",
            color=discord.Color.gold()
        )
        
        # Add additional tips for specific commands
        tips = {
            "commit": "💡 **Tip:** Use descriptive commit messages in present tense",
            "push": "💡 **Tip:** Always pull before pushing to avoid conflicts",
            "merge": "💡 **Tip:** Use --no-ff for merge commits to preserve branch history",
            "rebase": "⚠️ **Warning:** Never rebase commits that have been pushed to shared repos"
        }
        
        if command in tips:
            embed.add_field(name="Additional Info", value=tips[command], inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="encode", help="Encode text to various formats")
    @app_commands.describe(
        text="Text to encode",
        format="Encoding format (base64, url, hex, binary)"
    )
    async def encode_text(self, ctx: commands.Context, format: str, *, text: str):
        """Encode text to various formats"""
        import base64
        import urllib.parse
        
        format = format.lower()
        
        try:
            if format == "base64":
                encoded = base64.b64encode(text.encode()).decode()
            elif format == "url":
                encoded = urllib.parse.quote(text)
            elif format == "hex":
                encoded = text.encode().hex()
            elif format == "binary":
                encoded = ' '.join(format(ord(char), '08b') for char in text)
            else:
                await ctx.send("❌ Supported formats: base64, url, hex, binary")
                return
            
            embed = discord.Embed(
                title=f"🔐 Text Encoded ({format.upper()})",
                color=discord.Color.blue()
            )
            embed.add_field(name="Original", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name="Encoded", value=f"```\n{encoded}\n```", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Encoding failed: {str(e)}")

    @commands.hybrid_command(name="decode", help="Decode text from various formats")
    @app_commands.describe(
        text="Text to decode",
        format="Decoding format (base64, url, hex)"
    )
    async def decode_text(self, ctx: commands.Context, format: str, *, text: str):
        """Decode text from various formats"""
        import base64
        import urllib.parse
        
        format = format.lower()
        
        try:
            if format == "base64":
                decoded = base64.b64decode(text.encode()).decode()
            elif format == "url":
                decoded = urllib.parse.unquote(text)
            elif format == "hex":
                decoded = bytes.fromhex(text).decode()
            else:
                await ctx.send("❌ Supported formats: base64, url, hex")
                return
            
            embed = discord.Embed(
                title=f"🔓 Text Decoded ({format.upper()})",
                color=discord.Color.green()
            )
            embed.add_field(name="Encoded", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name="Decoded", value=f"```\n{decoded}\n```", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Decoding failed: {str(e)}")

    @commands.hybrid_command(name="hash", help="Generate hash values for text")
    @app_commands.describe(
        text="Text to hash",
        algorithm="Hash algorithm (md5, sha1, sha256, sha512)"
    )
    async def hash_text(self, ctx: commands.Context, algorithm: str, *, text: str):
        """Generate hash values using different algorithms"""
        import hashlib
        
        algorithm = algorithm.lower()
        
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5(text.encode())
            elif algorithm == "sha1":
                hash_obj = hashlib.sha1(text.encode())
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256(text.encode())
            elif algorithm == "sha512":
                hash_obj = hashlib.sha512(text.encode())
            else:
                await ctx.send("❌ Supported algorithms: md5, sha1, sha256, sha512")
                return
            
            hash_value = hash_obj.hexdigest()
            
            embed = discord.Embed(
                title=f"🔒 {algorithm.upper()} Hash",
                color=discord.Color.purple()
            )
            embed.add_field(name="Input", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name="Hash", value=f"```\n{hash_value}\n```", inline=False)
            
            # Security note for MD5
            if algorithm == "md5":
                embed.add_field(
                    name="⚠️ Security Note", 
                    value="MD5 is cryptographically broken. Use SHA-256 or higher for security.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Hashing failed: {str(e)}")

    @commands.hybrid_command(name="json", help="Format and validate JSON")
    @app_commands.describe(json_text="JSON text to format/validate")
    async def format_json(self, ctx: commands.Context, *, json_text: str):
        """Format and validate JSON"""
        import json
        
        try:
            # Remove code block formatting if present
            if json_text.startswith("```") and json_text.endswith("```"):
                json_text = json_text[3:-3]
                if json_text.startswith("json\n"):
                    json_text = json_text[5:]
            
            # Parse and format JSON
            parsed = json.loads(json_text)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ Valid JSON - Formatted",
                color=discord.Color.green()
            )
            
            # Truncate if too long
            if len(formatted) > 1800:
                formatted = formatted[:1800] + "..."
                embed.add_field(
                    name="⚠️ Note", 
                    value="Output was truncated due to length",
                    inline=False
                )
            
            embed.add_field(
                name="Formatted JSON", 
                value=f"```json\n{formatted}\n```", 
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except json.JSONDecodeError as e:
            embed = discord.Embed(
                title="❌ Invalid JSON",
                description=f"**Error:** {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Processing failed: {str(e)}")

    @commands.hybrid_command(name="color", help="Convert between color formats")
    @app_commands.describe(
        color="Color value (hex: #FF5733, rgb: 255,87,51, name: red)"
    )
    async def color_convert(self, ctx: commands.Context, *, color: str):
        """Convert between different color formats"""
        color = color.strip()
        
        try:
            r, g, b = 0, 0, 0
            
            # Parse different color formats
            if color.startswith('#'):
                # Hex color
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
            elif ',' in color:
                # RGB format
                rgb_values = [int(x.strip()) for x in color.split(',')]
                if len(rgb_values) != 3:
                    raise ValueError("RGB format should be: r,g,b")
                r, g, b = rgb_values
            else:
                # Color names
                color_names = {
                    'red': (255, 0, 0), 'green': (0, 128, 0), 'blue': (0, 0, 255),
                    'yellow': (255, 255, 0), 'orange': (255, 165, 0), 'purple': (128, 0, 128),
                    'pink': (255, 192, 203), 'black': (0, 0, 0), 'white': (255, 255, 255),
                    'gray': (128, 128, 128), 'brown': (165, 42, 42), 'cyan': (0, 255, 255)
                }
                if color.lower() in color_names:
                    r, g, b = color_names[color.lower()]
                else:
                    await ctx.send("❌ Invalid color format. Use hex (#FF5733), RGB (255,87,51), or color name.")
                    return
            
            # Validate RGB values
            if not all(0 <= val <= 255 for val in [r, g, b]):
                await ctx.send("❌ RGB values must be between 0 and 255.")
                return
            
            # Convert to different formats
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            hsl_h, hsl_s, hsl_l = rgb_to_hsl(r, g, b)
            
            embed = discord.Embed(
                title="🎨 Color Conversion",
                color=discord.Color.from_rgb(r, g, b)
            )
            embed.add_field(name="Hex", value=hex_color, inline=True)
            embed.add_field(name="RGB", value=f"rgb({r}, {g}, {b})", inline=True)
            embed.add_field(name="HSL", value=f"hsl({hsl_h}°, {hsl_s}%, {hsl_l}%)", inline=True)
            embed.add_field(name="CSS RGB", value=f"rgb({r}, {g}, {b})", inline=True)
            embed.add_field(name="CSS RGBA", value=f"rgba({r}, {g}, {b}, 1.0)", inline=True)
            embed.add_field(name="Decimal", value=f"{(r << 16) + (g << 8) + b}", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Color conversion failed: {str(e)}")

    @commands.hybrid_command(name="uuid", help="Generate various types of UUIDs")
    @app_commands.describe(version="UUID version (1, 4) or type (random, time)")
    async def generate_uuid(self, ctx: commands.Context, version: str = "4"):
        """Generate UUIDs"""
        import uuid
        
        try:
            if version.lower() in ["4", "random"]:
                generated_uuid = str(uuid.uuid4())
                uuid_type = "Random (Version 4)"
            elif version.lower() in ["1", "time"]:
                generated_uuid = str(uuid.uuid1())
                uuid_type = "Time-based (Version 1)"
            else:
                await ctx.send("❌ Supported versions: 1 (time-based), 4 (random)")
                return
            
            embed = discord.Embed(
                title="🆔 Generated UUID",
                color=discord.Color.blue()
            )
            embed.add_field(name="Type", value=uuid_type, inline=True)
            embed.add_field(name="UUID", value=f"```\n{generated_uuid}\n```", inline=False)
            embed.add_field(name="Format", value="8-4-4-4-12 hexadecimal digits", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ UUID generation failed: {str(e)}")

    @commands.hybrid_command(name="timestamp", help="Convert between timestamp formats")
    @app_commands.describe(
        timestamp="Unix timestamp or 'now' for current time",
        format="Output format (unix, iso, discord, readable)"
    )
    async def timestamp_convert(self, ctx: commands.Context, timestamp: str = "now", format: str = "all"):
        """Convert between different timestamp formats"""
        from datetime import datetime, timezone
        
        try:
            if timestamp.lower() == "now":
                dt = datetime.now(timezone.utc)
            else:
                # Try to parse as unix timestamp
                unix_time = int(timestamp)
                dt = datetime.fromtimestamp(unix_time, timezone.utc)
            
            unix_timestamp = int(dt.timestamp())
            iso_format = dt.isoformat()
            readable = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            discord_format = f"<t:{unix_timestamp}:F>"
            
            embed = discord.Embed(
                title="⏰ Timestamp Conversion",
                color=discord.Color.blue()
            )
            
            if format.lower() in ["all", "unix"]:
                embed.add_field(name="Unix Timestamp", value=f"`{unix_timestamp}`", inline=False)
            if format.lower() in ["all", "iso"]:
                embed.add_field(name="ISO 8601", value=f"`{iso_format}`", inline=False)
            if format.lower() in ["all", "readable"]:
                embed.add_field(name="Readable", value=readable, inline=False)
            if format.lower() in ["all", "discord"]:
                embed.add_field(name="Discord Format", value=f"{discord_format} → {discord_format}", inline=False)
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Invalid timestamp. Use unix timestamp or 'now'.")
        except Exception as e:
            await ctx.send(f"❌ Conversion failed: {str(e)}")

def rgb_to_hsl(r, g, b):
    """Convert RGB to HSL"""
    r, g, b = r/255.0, g/255.0, b/255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    h, s, l = 0, 0, (max_val + min_val) / 2

    if max_val == min_val:
        h = s = 0  # achromatic
    else:
        d = max_val - min_val
        s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        elif max_val == b:
            h = (r - g) / d + 4
        h /= 6

    return int(h * 360), int(s * 100), int(l * 100)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle hangman game responses"""
        if message.author.bot:
            return

        if message.channel.id in self.hangman_games:
            game = self.hangman_games[message.channel.id]
            
            content = message.content.upper()
            if len(content) == 1 and content.isalpha():
                if content in game["guessed"]:
                    await message.channel.send("You already guessed that letter!")
                    return

                game["guessed"].add(content)
                
                if content not in game["word"]:
                    game["tries"] -= 1

                word = game["word"]
                guessed = game["guessed"]
                tries = game["tries"]

                display = " ".join(letter if letter in guessed else "_" for letter in word)
                
                if tries == 0:
                    await message.channel.send(f"Game Over! The word was: {word}")
                    del self.hangman_games[message.channel.id]
                elif "_" not in display.replace(" ", ""):
                    await message.channel.send(f"🎉 Congratulations! You got it: {word}")
                    del self.hangman_games[message.channel.id]
                else:
                    embed = discord.Embed(
                        title="🎯 Hangman - Programming Edition",
                        description=f"```\n{display}\n```\nTries left: {tries}",
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
