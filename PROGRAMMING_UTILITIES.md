# 💻 Programming Utilities - CodeVerse Bot

## 🎯 Overview

CodeVerse Bot now includes **12 powerful programming utility commands** that make it an essential tool for developers. These commands provide instant access to common development resources, code snippets, and utilities.

---

## 📄 Code Snippets (`?snippet` / `/snippet`)

**Get ready-to-use code for common algorithms and patterns**

### Supported Languages
- **Python** - QuickSort, Binary Search, Fibonacci, API requests, File operations
- **JavaScript** - QuickSort, Fetch API, Debounce, Deep Clone
- **Java** - QuickSort with partitioning, Singleton pattern
- **C++** - Binary Search, Linked List implementation

### Example Usage
```
?snippet python quicksort
?snippet javascript fetch_api
?snippet java singleton
?snippet cpp linked_list
```

### Sample Output
```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

---

## 🔍 Regex Patterns (`?regex` / `/regex`)

**Access common regex patterns for validation**

### Available Patterns
| Pattern | Description | Example |
|---------|-------------|---------|
| `email` | Email validation | john.doe@example.com |
| `phone` | Phone number (with international support) | +1 555-123-4567 |
| `url` | URL validation | https://www.example.com/path |
| `ip` | IPv4 address | 192.168.1.1 |
| `hex_color` | Hex color codes | #FF5733 or #F53 |
| `credit_card` | Credit card numbers | Major card types |
| `password` | Strong password | 8+ chars, mixed case, special |

### Example Usage
```
?regex email          # Shows email regex pattern
?regex                # Lists all available patterns
```

---

## 📊 Big O Complexity (`?bigO` / `/bigO`)

**Learn algorithm complexity with visual explanations**

### Available Complexities
- **O(1)** - Constant time (with ASCII graph)
- **O(log n)** - Logarithmic time
- **O(n)** - Linear time (with ASCII graph)
- **O(n log n)** - Linearithmic time
- **O(n²)** - Quadratic time (with ASCII graph)
- **O(n³)** - Cubic time
- **O(2^n)** - Exponential time
- **O(n!)** - Factorial time

### Example Usage
```
?bigO                 # Shows all complexities ordered
?bigO n²              # Explains quadratic time complexity
```

### Sample Output
```
📊 Big O Notation: O(n²)
Quadratic Time - Time increases quadratically. Example: Bubble sort, nested loops.

Graph:
Time |         ●
     |      ●
     |   ●
     | ●
     |●
     |___________
          Input Size
```

---

## 🌐 HTTP Status Codes (`?http` / `/http`)

**Quick reference for HTTP status codes with color coding**

### Coverage
- **2xx Success** - 200, 201, 204 (Green)
- **4xx Client Error** - 400, 401, 403, 404, 405, 409, 429 (Orange)
- **5xx Server Error** - 500, 502, 503 (Red)

### Example Usage
```
?http                 # Shows common status codes
?http 404             # Explains "Not Found" error
?http 500             # Explains "Internal Server Error"
```

---

## 📚 Git Commands (`?git` / `/git`)

**Complete Git reference with professional tips**

### Command Categories
- **Basic:** init, clone, add, commit, push, pull, status, log
- **Advanced:** branch, checkout, merge, rebase, stash, reset

### Example Usage
```
?git                  # Shows all commands by category
?git commit           # Shows commit syntax and tips
?git rebase           # Shows rebase with warning about shared repos
```

### Sample Output
```bash
git commit -m 'message' - Commit staged changes

💡 Tip: Use descriptive commit messages in present tense
```

---

## 🔐 Text Encoding/Decoding (`?encode` / `?decode`)

**Convert text between various formats**

### Supported Formats
- **Base64** - Standard base64 encoding
- **URL** - URL percent encoding
- **Hex** - Hexadecimal representation
- **Binary** - Binary representation (encode only)

### Example Usage
```
?encode base64 Hello World
?decode hex 48656c6c6f
?encode url https://example.com?q=hello world
```

---

## 🔒 Hash Generation (`?hash` / `/hash`)

**Generate cryptographic hashes with security notes**

### Algorithms
- **MD5** - ⚠️ With security warning
- **SHA1** - Legacy support
- **SHA256** - Recommended
- **SHA512** - High security

### Example Usage
```
?hash sha256 my secret text
?hash md5 password123        # Shows security warning
```

---

## ✅ JSON Formatter (`?json` / `/json`)

**Validate and format JSON with error detection**

### Features
- **Syntax validation** with detailed error messages
- **Pretty formatting** with 2-space indentation
- **Code block handling** (removes ```json blocks)
- **Length truncation** for large objects
- **Unicode preservation**

### Example Usage
```
?json {"name": "test", "value": 123, "nested": {"key": "value"}}
```

### Error Handling
```
❌ Invalid JSON
Error: Expecting ',' delimiter: line 1 column 15 (char 14)
```

---

## 🎨 Color Converter (`?color` / `/color`)

**Convert between all color formats**

### Input Formats
- **Hex:** #FF5733, #F53
- **RGB:** 255,87,51
- **Color Names:** red, blue, green, etc. (12 supported)

### Output Formats
- Hex, RGB, HSL, CSS RGB/RGBA, Decimal value
- **Live preview** using embed color

### Example Usage
```
?color #FF5733
?color 255,87,51
?color red
```

### Sample Output
```
🎨 Color Conversion

Hex: #FF5733
RGB: rgb(255, 87, 51)
HSL: hsl(14°, 100%, 60%)
CSS RGBA: rgba(255, 87, 51, 1.0)
Decimal: 16733235
```

---

## 🆔 UUID Generator (`?uuid` / `/uuid`)

**Generate standard UUIDs**

### Versions
- **Version 1** (time-based) - Includes MAC address and timestamp
- **Version 4** (random) - Cryptographically secure random

### Example Usage
```
?uuid                 # Generates v4 (random) by default
?uuid 4               # Random UUID
?uuid 1               # Time-based UUID
?uuid random          # Same as v4
?uuid time            # Same as v1
```

### Sample Output
```
🆔 Generated UUID
Type: Random (Version 4)
UUID: 550e8400-e29b-41d4-a716-446655440000
Format: 8-4-4-4-12 hexadecimal digits
```

---

## ⏰ Timestamp Converter (`?timestamp` / `/timestamp`)

**Convert between timestamp formats**

### Input Options
- **Unix timestamp** - 1693958400
- **'now'** - Current time

### Output Formats
- **Unix** - 1693958400
- **ISO 8601** - 2023-09-05T20:00:00+00:00
- **Human readable** - 2023-09-05 20:00:00 UTC
- **Discord format** - `<t:1693958400:F>` with live preview

### Example Usage
```
?timestamp now
?timestamp 1693958400
?timestamp now unix     # Only show unix format
```

---

## 🚀 Why These Utilities Matter

### **Developer Productivity**
- **Instant access** to common code patterns
- **No need to Google** basic regex patterns
- **Quick reference** for HTTP codes and Git commands

### **Learning & Teaching**
- **Visual explanations** for Big O complexity
- **Interactive examples** for all utilities
- **Professional best practices** included

### **Team Collaboration**
- **Consistent code standards** with snippet templates
- **Shared reference point** for common patterns
- **Educational tool** for junior developers

### **Professional Quality**
- **Error handling** for all edge cases
- **Security notes** for cryptographic functions
- **Industry-standard formats** and practices

---

## 🛠️ Technical Implementation

### **Performance Optimized**
- Efficient regex compilation
- Minimal memory footprint
- Fast response times (<100ms)

### **User-Friendly Design**
- Clear error messages
- Helpful usage examples
- Consistent embed formatting

### **Extensible Architecture**
- Easy to add new code snippets
- Simple pattern additions
- Configurable data structures

---

**This comprehensive utility suite makes CodeVerse Bot an essential tool for any programming Discord server, rivaling dedicated development tools and productivity bots!**
