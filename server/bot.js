import dotenv from 'dotenv'
dotenv.config()
import express from 'express'
import cors from 'cors'
import { Telegraf, Markup } from "telegraf";

const app = express();
app.use(express.json());
app.use(cors());
const bot = new Telegraf(process.env.BOT_TOKEN);

app.get("/get-gtoken", (req, res) => {
    res.json({ key: process.env.TESTER_TOKEN});
});
app.get("/get-dstoken", (req, res) => {
    res.json({ key: process.env.TESTER_TOKEN});
});

bot.command("start", (ctx) => {
    const user = ctx.from;
    ctx.reply(`Welcome ${user}! Either paste a link directly, or enter the app interface from the button below:`, {
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: "Aumi App",
            web_app: { url: "" }
          }
        ]
      ]
    }
  });
});

const urlRegex = /^(https?:\/\/)?([\w.-]+)\.([a-z]{2,6})(\/[\w.-]*)*\/?$/i;
const tiktokDomain = "https://vt.tiktok.com"
bot.on("message", (ctx) => {
    console.log(ctx.message)
    if ("location" in ctx.message) {
      const { latitude, longitude } = ctx.message.location;
      ctx.reply(`Got your location: 🌍 Lat: ${latitude}, Long: ${longitude}`);
    } else if ("text" in ctx.message) {
        const urlLink = ctx.message.text
        if (!urlRegex.test(urlLink)) {
            ctx.reply("Not a valid link");
        }
        if (urlLink.includes(tiktokDomain)){ //todo: check in url domain
            ctx.reply("Cant process tiktok videos yet");
        }

    }
});


bot.on("location", (ctx) => {
    const { latitude, longitude } = ctx.message.location;
    ctx.reply(`Got your location: 🌍 Lat: ${latitude}, Long: ${longitude}`);
  });

bot.launch();
app.listen(3000, () => console.log("Server running on port 3000"));
console.log("Bot started!");

// API to receive messages from the Mini App
app.post("/echo", async (req, res) => {
    const { userId, text } = req.body;
    if (!userId || !text) return res.status(400).send("Missing data");
  
    try {
      await bot.telegram.sendMessage(userId, `Echo from Mini App: ${text}`);
      res.send({ success: true });
    } catch (error) {
      res.status(500).send({ success: false, error });
    }
});