import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin")
CHANNEL_1_ID = os.getenv("CHANNEL_1_ID", "@Cyber_Shield_official")
CHANNEL_2_ID = os.getenv("CHANNEL_2_ID", "@fegasus_1")

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Mock Database (In real projects, use SQLite or MongoDB/Firebase)
# user_id: {"balance": 0, "referred_by": None, "referrals": 0}
user_db = {}

# --- Helper Functions ---
async def check_membership(user_id: int) -> bool:
    """Checks if the user has joined both mandatory channels."""
    allowed_statuses = ["member", "administrator", "creator"]
    try:
        member1 = await bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        member2 = await bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        return member1.status in allowed_statuses and member2.status in allowed_statuses
    except Exception as e:
        logging.error(f"Error checking membership: {e}")
        return False

# --- Keyboards ---
def get_join_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Join Channel 1", url=f"https://t.me/{CHANNEL_1_ID.replace('@', '')}")],
        [InlineKeyboardButton(text="🔹 Join Channel 2", url=f"https://t.me/{CHANNEL_2_ID.replace('@', '')}")],
        [InlineKeyboardButton(text="✅ Verify Status", callback_data="verify_join")]
    ])

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Check Balance", callback_data="menu_balance")],
        [InlineKeyboardButton(text="🔗 Referral Link", callback_data="menu_referral")],
        [InlineKeyboardButton(text="💳 Payment Method", callback_data="menu_payment")],
        [InlineKeyboardButton(text="👨‍💻 Support Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])

def get_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔸 Bkash", callback_data="pay_bkash"),
            InlineKeyboardButton(text="🔸 Nagad", callback_data="pay_nagad")
        ],
        [
            InlineKeyboardButton(text="🔸 Rocket", callback_data="pay_rocket"),
            InlineKeyboardButton(text="🔸 Binance", callback_data="pay_binance")
        ],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]
    ])

# --- Handlers ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Initialize user in database if not exists
    if user_id not in user_db:
        user_db[user_id] = {"balance": 0, "referred_by": None, "referrals": 0}
        
        # Handle referral tracking from start link parameters (/start ref_12345)
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_id = int(args[1].replace("ref_", ""))
                # Prevent self-referral and check if referrer exists
                if referrer_id != user_id and referrer_id in user_db:
                    user_db[user_id]["referred_by"] = referrer_id
            except ValueError:
                pass

    # Force check membership on start
    if await check_membership(user_id):
        # If already joined, award points if they were referred by someone
        ref_by = user_db[user_id]["referred_by"]
        if ref_by and user_db[user_id].get("reward_given") is not True:
            user_db[ref_by]["balance"] += 10  # Example: 10 points per referral
            user_db[ref_by]["referrals"] += 1
            user_db[user_id]["reward_given"] = True
            try:
                await bot.send_message(ref_by, f"🎉 New Referral! User joined via your link. Added +10 to your balance.")
            except Exception:
                pass
                
        await message.answer("✨ Welcome back to Secure Surf Zone X!\nSelect an option from the menu below:", reply_markup=get_main_menu())
    else:
        await message.answer(
            "⚠️ Access Denied!\n\nYou must join our official channels to unlock the referral dashboard system.",
            reply_markup=get_join_keyboard()
        )

@dp.callback_query(F.data == "verify_join")
async def process_verify(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if await check_membership(user_id):
        # Process referral reward upon successful verification if applicable
        ref_by = user_db[user_id].get("referred_by")
        if ref_by and user_db[user_id].get("reward_given") is not True:
            user_db[ref_by]["balance"] += 10
            user_db[ref_by]["referrals"] += 1
            user_db[user_id]["reward_given"] = True
            try:
                await bot.send_message(ref_by, f"🎉 New Referral Verified! Added +10 to your balance.")
            except Exception:
                pass

        await callback.message.edit_text(
            "✅ Verification Successful!\nWelcome to the Main Dashboard. Choose your service:",
            reply_markup=get_main_menu()
        )
    else:
        await callback.answer("❌ Verification Failed! You haven't joined both channels yet.", show_alert=True)

# --- Dashboard Handlers ---

@dp.callback_query(F.data == "menu_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = user_db.get(user_id, {"balance": 0, "referrals": 0})
    
    text = (
        f"📊 **Your Account Summary**\n\n"
        f"💰 Current Balance: {data['balance']} Points\n"
        f"👥 Total Referrals: {data['referrals']} Users\n"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "menu_referral")
async def show_referral(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    
    # Generate unique referral link
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    text = (
        f"🔗 **Your Unique Referral Link**\n\n"
        f"Share this link with your friends. When they join and verify, you'll earn rewards!\n\n"
        f"`{ref_link}`"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.callback_query(F.data == "menu_payment")
async def show_payment_methods(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💳 **Select Your Preferred Payment Gateway:**\n\nPlease select one of the following providers to proceed with setup or payout.",
        reply_markup=get_payment_keyboard()
    )

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment_selection(callback: types.CallbackQuery):
    method = callback.data.replace("pay_", "").capitalize()
    await callback.answer(f"Selected Payment Method: {method}", show_alert=True)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✨ Main Dashboard Menu:\nSelect an option from the menu below:",
        reply_markup=get_main_menu()
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
