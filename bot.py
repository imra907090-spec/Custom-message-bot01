import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
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

# --- States for Withdrawal Flow ---
class WithdrawState(StatesGroup):
    waiting_for_method = State()
    waiting_for_number = State()
    waiting_for_amount = State()

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
        [InlineKeyboardButton(text="💳 Payment Method / Withdraw", callback_data="menu_payment")], # Updated Text
        [InlineKeyboardButton(text="💸 Withdraw Cash", callback_data="menu_withdraw")], # New Auto Inline Withdraw Button
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
            user_db[ref_by]["balance"] += 2  # Updated: Changed from 10 to 2 Taka per referral
            user_db[ref_by]["referrals"] += 1
            user_db[user_id]["reward_given"] = True
            try:
                await bot.send_message(ref_by, f"🎉 New Referral! User joined via your link. Added ৳2 to your balance.")
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
            user_db[ref_by]["balance"] += 2  # Updated: Changed from 10 to 2 Taka per referral
            user_db[ref_by]["referrals"] += 1
            user_db[user_id]["reward_given"] = True
            try:
                await bot.send_message(ref_by, f"🎉 New Referral Verified! Added ৳2 to your balance.")
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
        f"💰 Current Balance: ৳{data['balance']}\n"
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
        f"Share this link with your friends. When they join and verify, you'll earn ৳2 rewards!\n\n"
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
async def process_payment_selection(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.replace("pay_", "").capitalize()
    
    # Automatically forward to withdrawal flow when they click a payment method
    await state.update_data(withdraw_method=method)
    await callback.message.answer(f"Selected Payment Method: {method}\n\n📝 Please enter your {method} Account Number/ID:")
    await state.set_state(WithdrawState.waiting_for_number)
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✨ Main Dashboard Menu:\nSelect an option from the menu below:",
        reply_markup=get_main_menu()
    )

# --- New Automatic Withdraw System Handlers ---

@dp.callback_query(F.data == "menu_withdraw")
async def start_withdraw_flow(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💸 **Withdrawal System**\n\nPlease select your payment gateway to withdraw money:",
        reply_markup=get_payment_keyboard()
    )

@dp.message(WithdrawState.waiting_for_number)
async def process_withdraw_number(message: types.Message, state: FSMContext):
    account_number = message.text.strip()
    await state.update_data(account_number=account_number)
    
    user_id = message.from_user.id
    current_balance = user_db.get(user_id, {}).get("balance", 0)
    
    await message.answer(f"✅ Number Saved: `{account_number}`\n\n💰 Your Current Balance is ৳{current_balance}.\nHow much do you want to withdraw? Enter amount in digits:")
    await state.set_state(WithdrawState.waiting_for_amount)

@dp.message(WithdrawState.waiting_for_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {"balance": 0})
    
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid Amount! Please enter a valid number (e.g., 50, 100):")
        return

    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Please try again:")
        return
        
    if amount > user_data["balance"]:
        await message.answer(f"❌ Insufficient Balance! Your current balance is ৳{user_data['balance']}. Please enter a smaller amount:")
        return

    # Deduct the amount and save remaining balance
    user_db[user_id]["balance"] -= amount
    
    # Get saved payment method and number
    data = await state.get_data()
    method = data.get("withdraw_method")
    account_number = data.get("account_number")
    
    # Notify User
    await message.answer(
        f"✅ **Withdraw Request Submitted Successfully!**\n\n"
        f"💵 Amount: ৳{amount}\n"
        f"🏦 Method: {method}\n"
        f"📱 Account No: `{account_number}`\n\n"
        f"Remaining Balance: ৳{user_db[user_id]['balance']}\n"
        f"Admin will process your payment soon.",
        reply_markup=get_main_menu()
    )
    
    # Notify Admin (Sends full detail to Admin ID)
    admin_text = (
        f"🚨 **New Withdrawal Request Received!**\n\n"
        f"👤 User: {message.from_user.full_name} (ID: `{user_id}`)\n"
        f" username: @{message.from_user.username if message.from_user.username else 'None'}\n"
        f"💵 Amount: **৳{amount}**\n"
        f"🏦 Method: **{method}**\n"
        f"📱 Account Number: `{account_number}`\n"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        logging.error(f"Failed to send withdrawal notice to admin: {e}")
        
    # Clear FSM State
    await state.clear()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
