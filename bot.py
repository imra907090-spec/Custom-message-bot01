import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # আপনার টেলিগ্রাম আইডি

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ইউজার ডাটা রাখার জন্য
USERS_DB = set()

# চ্যানেল কনফিগারেশন (বোটকে এই চ্যানেলগুলোতে অ্যাডমিন বানাতে হবে)
CHANNEL_1 = "@+LuFONHIYykA2OWNl" 
CHANNEL_2 = "@Cyber_Shield_official"
CHANNEL_1_LINK = "https://t.me/+LuFONHIYykA2OWNl"
CHANNEL_2_LINK = "https://t.me/Cyber_Shield_official"

# FSM স্টেটস (অ্যাডমিন প্যানেল এবং সাবমিট ট্র্যাকিংয়ের জন্য)
class BotStates(StatesGroup):
    waiting_for_submit = State()      # ইউজার যখন সাবমিট বাটনে চাপ দিয়ে ফাইল পাঠানোর অপেক্ষায় থাকবে

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_channels = State()

# চ্যানেলে জয়েন আছে কিনা চেক করার ফাংশন
async def check_user_joined(user_id: int) -> bool:
    try:
        member1 = await bot.get_chat_member(chat_id=CHANNEL_1, user_id=user_id)
        member2 = await bot.get_chat_member(chat_id=CHANNEL_2, user_id=user_id)
        
        valid_statuses = ['member', 'administrator', 'creator']
        if member1.status in valid_statuses and member2.status in valid_statuses:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return False

# --- কিবোর্ডসমূহ ---

# ১. শুরুর ফোর্স জয়েন কিবোর্ড
def get_join_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📢 চ্যানেল ১-এ জয়েন করুন", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton(text="📢 চ্যানেল ২-এ জয়েন করুন", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data="verify_join")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ২. ভেরিফাই হওয়ার পরের ইনস্টাগ্রাম কিবোর্ড
def get_instagram_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📸 ইনস্টাগ্রাম", callback_data="instagram_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ৩. ইনস্টাগ্রামে চাপ দেওয়ার পর "ইনস্টাগ্রাম টু এফ অ্যাকাউন্ট" কিবোর্ড
def get_instagram_2fa_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔐 ইনস্টাগ্রাম টু এফ অ্যাকাউন্ট", callback_data="instagram_2fa")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ৪. ইনস্টাগ্রাম টু এফ-এ চাপ দেওয়ার পর "সাবমিট" কিবোর্ড
def get_submit_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📤 সাবমিট", callback_data="submit_files")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# অ্যাডমিন প্যানেল কিবোর্ড
def get_admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📊 মোট ইউজার", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 ব্রডকাস্ট", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⚙️ চ্যানেল পরিবর্তন", callback_data="admin_channels")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- হ্যান্ডলারস ---

# /start কমান্ড
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # যেকোনো আগের স্টেট ক্লিয়ার করা
    USERS_DB.add(message.from_user.id)
    is_joined = await check_user_joined(message.from_user.id)
    
    if is_joined:
        await message.answer(
            f"👋 হ্যালো {message.from_user.first_name}!\n"
            "আপনি অলরেডি ভেরিফাইড ইউজার। নিচের অপশনটি ব্যবহার করুন:",
            reply_markup=get_instagram_keyboard()
        )
    else:
        await message.answer(
            "⚠️ **অ্যাক্সেস ব্লকড!**\n\n"
            "বোটটি ব্যবহার করতে আপনাকে অবশ্যই আমাদের নিচের দুটি চ্যানেলে জয়েন করতে হবে। "
            "জয়েন করার পর নিচের **'ভেরিফাই করুন'** বাটনে ক্লিক করুন evenings।",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )

# ভেরিফাই বাটন অ্যাকশন
@dp.callback_query(F.data == "verify_join")
async def verify_callback(callback: types.CallbackQuery):
    is_joined = await check_user_joined(callback.from_user.id)
    
    if is_joined:
        await callback.message.edit_text(
            "✅ ভেরিফিকেশন সফল হয়েছে!\nনিচের বাটনে ক্লিক করুন:",
            reply_markup=get_instagram_keyboard()
        )
    else:
        await callback.answer(
            "❌ আপনি এখনো দুটি চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।", 
            show_alert=True
        )

# ইনস্টাগ্রাম বাটন অ্যাকশন
@dp.callback_query(F.data == "instagram_main")
async def instagram_main_callback(callback: types.CallbackQuery):
    is_joined = await check_user_joined(callback.from_user.id)
    if not is_joined:
        await callback.answer("⚠️ আপনি চ্যানেল থেকে লেফট নিয়েছেন! আবার জয়েন করুন।", show_alert=True)
        return
        
    await callback.message.edit_text(
        "📂 ইনস্টাগ্রাম মেন্যু:\nনিচের বাটনটি সিলেক্ট করুন।",
        reply_markup=get_instagram_2fa_keyboard()
    )

# ইনস্টাগ্রাম টু এফ অ্যাকাউন্ট বাটন অ্যাকশন
@dp.callback_query(F.data == "instagram_2fa")
async def instagram_2fa_callback(callback: types.CallbackQuery):
    is_joined = await check_user_joined(callback.from_user.id)
    if not is_joined:
        await callback.answer("⚠️ অনুগ্রহ করে প্রথমে চ্যানেলে জয়েন থাকুন।", show_alert=True)
        return

    # এখানে এখন সাবমিট বাটন শো করবে
    await callback.message.edit_text(
        "🔐 **ইনস্টাগ্রাম টু এফ অ্যাকাউন্ট সেকশন**\n\n"
        "আপনার ফাইল সাবমিট করতে নিচের **'সাবমিট'** বাটনে ক্লিক করুন।",
        reply_markup=get_submit_keyboard()
    )
    await callback.answer()

# সাবমিট বাটন অ্যাকশন
@dp.callback_query(F.data == "submit_files")
async def submit_files_callback(callback: types.CallbackQuery, state: FSMContext):
    is_joined = await check_user_joined(callback.from_user.id)
    if not is_joined:
        await callback.answer("⚠️ অনুগ্রহ করে প্রথমে চ্যানেলে জয়েন থাকুন।", show_alert=True)
        return

    # ইউজারকে ফাইল পাঠানোর স্টেটে নেওয়া হচ্ছে
    await state.set_state(BotStates.waiting_for_submit)
    
    await callback.message.edit_text(
        "📥 **ফাইল সাবমিট মোড অন হয়েছে!**\n\n"
        "এখন আপনি আপনার যেকোনো ফাইল (ফটো, ভিডিও, ডকুমেন্ট বা অডিও) এখানে পাঠাতে পারেন।"
    )
    await callback.answer()

# ফাইল রিসিভার এবং অটো রিপ্লাই হ্যান্ডলার (ইউজার যখন সাবমিট মোডে থাকবে)
@dp.message(BotStates.waiting_for_submit, F.document | F.photo | F.video | F.audio | F.voice)
async def handle_incoming_files(message: types.Message, state: FSMContext):
    is_joined = await check_user_joined(message.from_user.id)
    if not is_joined:
        await message.answer("⚠️ ফাইল পাঠাতে হলে প্রথমে চ্যানেলে জয়েন করে ভেরিফাই করুন!", reply_markup=get_join_keyboard())
        await state.clear()
        return

    # এখানে আপনি ফাইলটি ডাউনলোড করার বা অ্যাডমিনকে ফরোয়ার্ড করার কোড রাখতে পারেন।
    # উদাহরণস্বরূপ অ্যাডমিনকে ফরোয়ার্ড করতে চাইলে: 
    # await message.forward(chat_id=ADMIN_ID)

    # অটো রিপ্লাই মেসেজ
    await message.reply(
        "✅ **আপনার ফাইলটি সফলভাবে রিসিভ করা হয়েছে!**\n\n"
        "আমাদের টিম খুব শীঘ্রই এটি রিভিউ করবে। ধন্যবাদ আমাদের সাথে থাকার জন্য। 😊"
    )
    
    # ফাইল পাঠানো শেষ হলে স্টেট ক্লিয়ার করে দেওয়া হচ্ছে যাতে পরবর্তীতে আবার নরমালি বাটন চাপতে পারে
    await state.clear()


# --- অ্যাডমিন প্যানেল সেকশন ---

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("⚙️ **স্বাগতম অ্যাডমিন প্যানেলে!**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer(f"📊 **বোটের বর্তমান অবস্থা:**\n👥 মোট ইউজার: {len(USERS_DB)} জন")
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("📢 যে মেসেজটি সবার কাছে পাঠাতে চান, তা এখন লিখে পাঠান:")
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("🚀 ব্রডকাস্ট শুরু হয়েছে...")
    success_count = 0
    for user_id in list(USERS_DB):
        try:
            await bot.send_message(chat_id=user_id, text=message.text)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"📢 ব্রডকাস্ট সম্পন্ন!\n✅ সফলভাবে পাঠানো হয়েছে: {success_count} জনের কাছে।")
    await state.clear()

@dp.callback_query(F.data == "admin_channels")
async def admin_channels_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer(
        "⚙️ নতুন চ্যানেল সেট করতে নিচের ফরম্যাটে লিখে পাঠান:\n\n"
        "`@চ্যানেল১|@চ্যানেল২|লিংক১|লিংক২`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_channels)
    await callback.answer()

@dp.message(AdminStates.waiting_for_channels)
async def process_channels_update(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    global CHANNEL_1, CHANNEL_2, CHANNEL_1_LINK, CHANNEL_2_LINK
    try:
        data = message.text.split("|")
        if len(data) == 4:
            CHANNEL_1, CHANNEL_2, CHANNEL_1_LINK, CHANNEL_2_LINK = [d.strip() for d in data]
            await message.answer("✅ চ্যানেল এবং লিংক সফলভাবে আপডেট করা হয়েছে!")
            await state.clear()
        else:
            await message.answer("❌ ফরম্যাট ঠিক নেই! আবার চেষ্টা করুন।")
    except Exception as e:
        await message.answer(f"❌ ভুল হয়েছে: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
