# 🚀 **Free Discord Bot Hosting Guide**

## 🎯 **Quick Setup (5 Minutes)**

### **Option 1: Railway (Recommended) 🚂**

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Your Bot**
   ```bash
   # Push your code to GitHub first
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. **Connect to Railway**
   - Click "Deploy from GitHub repo"
   - Select your bot repository
   - Railway will auto-detect Python

4. **Add Environment Variables**
   - Go to your project → Variables
   - Add these variables:
   ```
   DISCORD_TOKEN=your_new_bot_token_here
   GUILD_ID=1263067254153805905
   QUESTIONS_CHANNEL_ID=1398986762352857129
   STAFF_UPDATES_CHANNEL_ID=1401016150703210507
   LEADERBOARD_CHANNEL_ID=1400074508664049765
   SUGGESTIONS_CHANNEL_ID=1263071014279970826
   MOD_TOOLS_CHANNEL_ID=1396353386429026304
   BOT_COMMANDS_CHANNEL_ID=1263070079092789312
   JOINS_LEAVES_CHANNEL_ID=1263070188589547541
   SERVER_LOGS_CHANNEL_ID=1263434413581008956
   HOSTING_PLATFORM=railway
   PORT=8080
   ```

5. **Deploy & Monitor**
   - Railway will automatically deploy
   - Check logs for any errors
   - Your bot should come online!

---

### **Option 2: Render 🔄**

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Choose these settings:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
   ```

3. **Environment Variables**
   - Add the same variables as Railway
   - Set `HOSTING_PLATFORM=render`

---

### **Option 3: GitHub Codespaces (Development) 💻**

1. **Start Codespace**
   - Go to your GitHub repo
   - Click "Code" → "Codespaces" → "Create codespace"

2. **Run Bot**
   ```bash
   pip install -r requirements.txt
   python start_bot.py
   ```

3. **Keep Running**
   - Use tmux or screen to keep it running
   - Limited to 60 hours/month

---

## 🔧 **Optimization for Free Hosting**

### **1. Reduce Memory Usage**
Add this to your `.env`:
```
# Optimize for free hosting
XP_COOLDOWN_SECONDS=120
LEVEL_UP_BONUS_XP=15
```

### **2. Enable Sleep Mode (Save Hours)**
The bot will automatically sleep when inactive and wake up when needed.

### **3. Monitor Usage**
- Railway: Check your dashboard for usage
- Render: Monitor build minutes and uptime

---

## 🛡️ **Security Setup**

### **1. Environment Variables Only**
Never commit your `.env` file to GitHub!

### **2. Create `.gitignore`**
```
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
data/codeverse_bot.db
logs/
```

### **3. Use Production Token**
- Create a NEW bot token in Discord Developer Portal
- Use this new token for hosting
- The old token is compromised

---

## 📊 **Free Tier Limits**

| Platform | Hours/Month | Memory | Storage | Pros |
|----------|-------------|---------|---------|------|
| Railway | 500 hours | 512MB | 1GB | Easy setup, good performance |
| Render | 750 hours | 512MB | 1GB | More hours, reliable |
| Codespaces | 60 hours | 2GB | 10GB | Full dev environment |

---

## 🚨 **Important Notes**

### **⚠️ Before Deploying:**
1. **Get NEW Discord bot token** (current one is exposed)
2. **Test locally first**: `python start_bot.py`
3. **Commit to GitHub** (without .env file)
4. **Set up environment variables** on hosting platform

### **🔄 Staying Within Limits:**
- Bot automatically sleeps when inactive
- Uses efficient database operations
- Optimized memory usage for free tiers

### **📈 Monitoring Health:**
- Your bot has built-in health endpoints
- Check `https://your-app.railway.app/health`
- Monitor logs in platform dashboard

---

## 🎉 **You're Ready to Deploy!**

**Next Steps:**
1. ✅ Push code to GitHub
2. ✅ Choose hosting platform (Railway recommended)  
3. ✅ Set environment variables
4. ✅ Deploy and monitor
5. ✅ Enjoy your 24/7 Discord bot!

**Your bot will be online 24/7 and handle hundreds of users!** 🚀

---

## 🆘 **Troubleshooting**

### **Bot Won't Start:**
- Check environment variables are set correctly
- Verify Discord token is valid
- Check logs for error messages

### **Runs Out of Hours:**
- Use Railway + Render combination
- Deploy to multiple platforms with same code
- Implement sleep mode optimizations

### **Performance Issues:**
- Monitor memory usage in dashboard
- Optimize database queries if needed
- Consider upgrading to paid tier ($5/month)

**Need help?** Check the logs in your hosting platform dashboard!
