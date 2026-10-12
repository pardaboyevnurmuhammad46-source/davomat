import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command as TgCommand, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from config.models import Attendance, Grade, StudentProfile, User

dp = Dispatcher()

contact_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]],
    resize_keyboard=True,
)


async def get_user(message):
    return await User.objects.filter(telegram_id=message.from_user.id).afirst()


async def get_students(user):
    if user.role == User.Role.STUDENT:
        qs = StudentProfile.objects.filter(user=user)
    elif user.role == User.Role.PARENT:
        qs = StudentProfile.objects.filter(parents__user=user)
    else:
        return []
    return [s async for s in qs.select_related('user')]


@dp.message(CommandStart())
async def start(message: Message):
    if await get_user(message):
        await message.answer("Buyruqlar: /baholar, /davomat")
        return
    await message.answer("Telefon raqamingizni yuboring.", reply_markup=contact_kb)


@dp.message(F.contact)
async def contact(message: Message):
    if message.contact.user_id != message.from_user.id:
        await message.answer("Faqat o'zingizning raqamingizni yuboring.")
        return
    user = await User.objects.filter(phone__endswith=message.contact.phone_number[-9:]).afirst()
    if not user:
        await message.answer("Raqam tizimda topilmadi. Maktab ma'muriyatiga murojaat qiling.",
                             reply_markup=ReplyKeyboardRemove())
        return
    await User.objects.filter(telegram_id=message.from_user.id).exclude(pk=user.pk).aupdate(telegram_id=None)
    user.telegram_id = message.from_user.id
    await user.asave(update_fields=['telegram_id'])
    await message.answer("Ulandingiz. Buyruqlar: /baholar, /davomat", reply_markup=ReplyKeyboardRemove())


@dp.message(TgCommand("baholar"))
async def grades(message: Message):
    user = await get_user(message)
    if not user:
        await message.answer("Avval /start bosing.")
        return
    students = await get_students(user)
    if not students:
        await message.answer("Sizga bog'langan o'quvchi yo'q.")
        return
    for student in students:
        qs = Grade.objects.filter(student=student).select_related('subject').order_by('-date', '-id')[:10]
        rows = [f"{g.date} {g.subject.name}: {g.grade}" async for g in qs]
        name = student.user.get_full_name() or student.user.username
        await message.answer(f"{name}\n" + ("\n".join(rows) or "Baholar yo'q"))


@dp.message(TgCommand("davomat"))
async def attendance(message: Message):
    user = await get_user(message)
    if not user:
        await message.answer("Avval /start bosing.")
        return
    for student in await get_students(user):
        total = await Attendance.objects.filter(student=student).acount()
        present = await Attendance.objects.filter(student=student, status=Attendance.Status.PRESENT).acount()
        percent = round(present / total * 100, 1) if total else 100
        name = student.user.get_full_name() or student.user.username
        await message.answer(f"{name}: {total} ta darsdan {present} tasida qatnashgan ({percent}%)")


class Command(BaseCommand):
    help = "Telegram botni ishga tushirish"

    def handle(self, *args, **options):
        if not settings.BOT_TOKEN:
            raise CommandError("BOT_TOKEN .env da yo'q")
        logging.basicConfig(level=logging.INFO)
        asyncio.run(self.main())

    async def main(self):
        await dp.start_polling(Bot(token=settings.BOT_TOKEN))