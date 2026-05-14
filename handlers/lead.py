"""
Обработчики для формы лидогенерации
"""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from database import add_lead_to_db, get_leads_from_db
from states import FormStates
from utils.validators import validate_phone, validate_name, escape_markdown, escape_html

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start"""
    logger.info(f"Пользователь {message.from_user.id} начал填写 формы")
    
    # Сброс состояния FSM
    await state.clear()
    
    # Проверяем, что это не бот
    if message.from_user.is_bot:
        await message.answer("Боты не могут填写 формы")
        return
    
    # Начинаем форму с запроса имени
    await state.set_state(FormStates.name)
    await message.answer(
        "👋 Добро пожаловать! Я помогу вам оставить заявку.\n\n"
        "📝 Пожалуйста, введите ваше имя:"
    )


@router.message(FormStates.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Обработка имени пользователя"""
    logger.info(f"Получено имя от пользователя {message.from_user.id}: {message.text}")
    
    # Валидация имени
    is_valid, result = validate_name(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {result}\n\n📝 Пожалуйста, введите корректное имя:")
        return
    
    # Сохраняем имя в состояние
    await state.update_data(name=result)
    
    # Переходим к следующему шагу - запрос телефона
    await state.set_state(FormStates.phone)
    await message.answer(
        "📞 Отлично! Теперь введите ваш номер телефона:\n\n"
        "💡 Пример: +7 (999) 123-45-67 или 89001234567"
    )


@router.message(FormStates.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    """Обработка номера телефона"""
    logger.info(f"Получен телефон от пользователя {message.from_user.id}: {message.text}")
    
    # Валидация телефона
    is_valid, result = validate_phone(message.text)
    
    if not is_valid:
        await message.answer(
            f"❌ {result}\n\n"
            "📞 Пожалуйста, введите корректный номер телефона:\n"
            "💡 Пример: +7 (999) 123-45-67 или 89001234567"
        )
        return
    
    # Сохраняем телефон в состояние
    await state.update_data(phone=result)
    
    # Переходим к выбору услуги
    await state.set_state(FormStates.service)
    
    # Создаем inline-кнопки
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(text="🔧 Ремонт", callback_data="service:repair"),
        InlineKeyboardButton(text="💬 Консультация", callback_data="service:consultation"),
        InlineKeyboardButton(text="🚚 Доставка", callback_data="service:delivery"),
        InlineKeyboardButton(text="📋 Другое", callback_data="service:other")
    )
    keyboard_builder.adjust(2)
    
    await message.answer(
        "🏢 Выберите услугу:",
        reply_markup=keyboard_builder.as_markup()
    )


@router.callback_query(FormStates.service, F.data.startswith("service:"))
async def process_service(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора услуги"""
    logger.info(f"Пользователь {callback.from_user.id} выбрал услугу: {callback.data}")
    
    # Получаем service из callback_data
    service_data = callback.data.split(":")
    service = service_data[1]
    
    # Определяем текстовую метку услуги
    service_labels = {
        "repair": "🔧 Ремонт",
        "consultation": "💬 Консультация", 
        "delivery": "🚚 Доставка",
        "other": "📋 Другое"
    }
    
    service_label = service_labels.get(service, service)
    
    # Сохраняем услугу в состояние
    await state.update_data(service=service_label)
    
    # Удаляем предыдущее сообщение с кнопками
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        # Сообщение уже удалено или недоступно
        pass
    
    # Переходим к финальной сводке
    await state.set_state(FormStates.summary)
    
    # Получаем все данные из состояния
    user_data = await state.get_data()
    
    # Формируем сводку
    summary = (
        f"📋 **Сводка заявки:**\n\n"
        f"👤 **Имя:** {user_data['name']}\n"
        f"📞 **Телефон:** {user_data['phone']}\n"
        f"🏢 **Услуга:** {user_data['service']}\n\n"
        f"Нажмите кнопку ниже для отправки заявки администратору."
    )
    
    # Создаем кнопку отправки
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(text="✅ Отправить заявку", callback_data="submit_lead")
    )
    
    await callback.message.answer(
        summary,
        reply_markup=keyboard_builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN
    )


@router.callback_query(FormStates.summary, F.data == "submit_lead")
async def submit_lead(callback: CallbackQuery, state: FSMContext) -> None:
    """Отправка заявки администратору"""
    logger.info(f"Пользователь {callback.from_user.id} отправляет заявку")
    
    try:
        # Получаем все данные из состояния
        user_data = await state.get_data()
        
        # Проверяем, что все данные есть
        if not all(key in user_data for key in ['name', 'phone', 'service']):
            await callback.answer("❌ Ошибка: данные формы неполные", show_alert=True)
            return
        
        # Добавляем заявку в базу данных
        success = add_lead_to_db(
            name=user_data['name'],
            phone=user_data['phone'],
            service=user_data['service'],
            user_id=callback.from_user.id
        )
        
        if not success:
            await callback.answer("❌ Ошибка при сохранении заявки", show_alert=True)
            return
        
        # Формируем сообщение для администратора
        admin_message = (
            f"🔥 **Новая заявка!**\n\n"
            f"👤 **Имя:** {user_data['name']}\n"
            f"📞 **Телефон:** {user_data['phone']}\n"
            f"🏢 **Услуга:** {user_data['service']}\n"
            f"🆔 **ID пользователя:** {callback.from_user.id}\n"
            f"📱 **Пользователь:** @{callback.from_user.username or 'Нет username'}\n"
            f"⏰ **Время:** {callback.message.date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Отправляем сообщение администратору
        admin_id = Config.ADMIN_ID
        admin_sent = False
        
        try:
            await callback.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode=ParseMode.MARKDOWN
            )
            admin_sent = True
            logger.info(f"Заявка пользователя {callback.from_user.id} отправлена администратору {admin_id}")
        except TelegramBadRequest as e:
            if "user not found" in str(e):
                logger.error(f"Администратор с ID {admin_id} не найден")
                await callback.answer(
                    "❌ Ошибка: администратор не найден. "
                    "Пожалуйста, свяжитесь с разработчиком.",
                    show_alert=True
                )
            else:
                logger.error(f"Ошибка отправки сообщения администратору: {e}")
                await callback.answer(
                    "❌ Ошибка при отправке заявки администратору. "
                    "Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
        
        # Отправляем пользователю подтверждение
        if admin_sent:
            await callback.message.edit_text(
                "✅ **Заявка успешно отправлена!**\n\n"
                "Администратор свяжется с вами в ближайшее время.\n\n"
                f"📝 **Ваши данные:**\n"
                f"👤 Имя: {user_data['name']}\n"
                f"📞 Телефон: {user_data['phone']}\n"
                f"🏢 Услуга: {user_data['service']}",
                parse_mode=ParseMode.MARKDOWN
            )
            await callback.answer()
        else:
            await callback.message.edit_text(
                "⚠️ **Заявка сохранена, но не доставлена администратору.**\n\n"
                "Данные сохранены в базе. Пожалуйста, свяжитесь с администратором.",
                parse_mode=ParseMode.MARKDOWN
            )
            await callback.answer()
        
        # Очищаем состояние FSM
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при отправке заявки: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_form(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена заполнения формы"""
    logger.info(f"Пользователь {callback.from_user.id} отменил заполнение формы")
    
    await state.clear()
    
    try:
        await callback.message.edit_text(
            "❌ Форма отменена.\n\n"
            "Если передумаете, введите /start для начала заново."
        )
    except TelegramBadRequest:
        # Сообщение уже удалено
        pass
    
    await callback.answer()


@router.message(F.text == "/stats")
async def cmd_stats(message: Message) -> None:
    """Команда для просмотра статистики (только для админа)"""
    if message.from_user.id != Config.ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа")
        return
    
    try:
        # Получаем последние заявки
        leads = get_leads_from_db(limit=10)
        
        if not leads:
            await message.answer("📊 **Статистика заявок**\n\nНет активных заявок.")
            return
        
        stats_message = "📊 **Последние заявки:**\n\n"
        
        for i, lead in enumerate(leads, 1):
            created_at = lead['created_at'][:16]  # Формат YYYY-MM-DD HH:MM
            stats_message += (
                f"{i}. 📅 {created_at}\n"
                f"   👤 {lead['name']}\n"
                f"   📞 {lead['phone']}\n"
                f"   🏢 {lead['service']}\n"
                f"   👤 ID: {lead['user_id']}\n\n"
            )
        
        await message.answer(stats_message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message()
async def handle_unexpected_messages(message: Message, state: FSMContext) -> None:
    """Обработка неожиданных сообщений в процессе заполнения формы"""
    current_state = await state.get_state()
    
    if current_state and current_state != FormStates.__name__:
        # Если пользователь находится в процессе заполнения формы
        await message.answer(
            "⚠️ Пожалуйста, завершите или отмените текущую форму (/cancel)\n\n"
            f"Текущее состояние: {current_state}"
        )
    else:
        # Если пользователь не в процессе заполнения формы
        await message.answer(
            "🤖 Я бот для сбора заявок.\n\n"
            "Доступные команды:\n"
            "/start - начать заполнение формы\n"
            "/stats - статистика заявок (только для админа)"
        )