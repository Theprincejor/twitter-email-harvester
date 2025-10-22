"""
Extended Telegram Bot with Email Management
Adds ability to manage warmup and checkpoint emails via Telegram
"""
import os
import yaml
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from campaign_manager import CampaignManager
from email_manager import EmailListManager


# Conversation states
(WAITING_USERNAME, WAITING_CAMPAIGN, WAITING_SETTINGS_CONFIRM,
 WAITING_MAIL_PER_DAY, WAITING_STOP_CONFIRM, WAITING_CONTINUE_CONFIRM,
 WAITING_EMAIL_CAMPAIGN, WAITING_EMAIL_TYPE, WAITING_EMAIL_INPUT,
 WAITING_VIEW_CAMPAIGN, WAITING_VIEW_TYPE) = range(11)


class ExtendedTelegramBot:
    """Extended Telegram bot with email list management"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.bot_token = self.config['telegram']['bot_token']
        self.admin_chat_ids = set(self.config['telegram']['admin_chat_ids'])
        self.campaign_manager = CampaignManager(config_path)
        self.email_manager = EmailListManager()

        # Store user session data
        self.user_sessions = {}

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_chat_ids

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized. Contact admin.")
            return

        welcome_text = """
🤖 **Email Campaign Bot**

**Campaign Control:**
/start_process - Start a new campaign
/continue_process - Continue a paused campaign
/stop_process - Stop a running campaign
/status - View campaign status

**Email Management:**
/add_emails - Add warmup/checkpoint emails
/view_emails - View warmup/checkpoint emails
/clear_emails - Clear warmup/checkpoint emails

/settings - Configure campaign settings
/help - Show this help message
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start(update, context)

    # ========================================
    # CAMPAIGN CONTROL (same as before)
    # ========================================

    async def start_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start_process command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return ConversationHandler.END

        self.user_sessions[user_id] = {}
        await update.message.reply_text(
            "📝 Please enter the Twitter username (without @):"
        )
        return WAITING_USERNAME

    async def receive_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive Twitter username"""
        user_id = update.effective_user.id
        username = update.message.text.strip().lstrip('@')

        self.user_sessions[user_id]['twitter_username'] = username

        # Show campaign selection
        campaigns = self.campaign_manager.get_campaigns()
        keyboard = []
        for campaign in campaigns:
            campaign_config = self.campaign_manager.get_campaign_config(campaign)
            keyboard.append([
                InlineKeyboardButton(
                    f"{campaign_config['name']}",
                    callback_data=f"campaign_{campaign}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Twitter: @{username}\n\n📋 Select Campaign:",
            reply_markup=reply_markup
        )
        return WAITING_CAMPAIGN

    async def receive_campaign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive campaign selection"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        campaign_id = query.data.replace("campaign_", "")

        self.user_sessions[user_id]['campaign_id'] = campaign_id

        # Get campaign config
        campaign_config = self.campaign_manager.get_campaign_config(campaign_id)

        # Show settings options
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data="warmup_yes"),
                InlineKeyboardButton("❌ No", callback_data="warmup_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📧 Campaign: {campaign_config['name']}\n"
            f"📨 From: {campaign_config['smtp']['from_email']}\n\n"
            f"🔥 **Use Warmup & Checkpoint?**\n"
            f"This will send warmup emails first, then checkpoint emails periodically.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_SETTINGS_CONFIRM

    async def receive_warmup_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive warmup setting"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        use_warmup = query.data == "warmup_yes"

        self.user_sessions[user_id]['use_warmup_checkpoint'] = use_warmup

        # Show mail per day options
        keyboard = [
            [InlineKeyboardButton("50", callback_data="mpd_50")],
            [InlineKeyboardButton("100", callback_data="mpd_100")],
            [InlineKeyboardButton("500", callback_data="mpd_500")],
            [InlineKeyboardButton("1000", callback_data="mpd_1000")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ Warmup: {'Enabled' if use_warmup else 'Disabled'}\n\n"
            f"📊 **Emails per day:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_MAIL_PER_DAY

    async def receive_mail_per_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive mail per day setting and start campaign"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        mails_per_day = int(query.data.replace("mpd_", ""))

        session = self.user_sessions[user_id]
        campaign_id = session['campaign_id']
        twitter_username = session['twitter_username']
        use_warmup = session['use_warmup_checkpoint']

        # Show confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm & Start", callback_data="confirm_start"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        campaign_config = self.campaign_manager.get_campaign_config(campaign_id)

        await query.edit_message_text(
            f"📋 **Campaign Summary**\n\n"
            f"🐦 Twitter: @{twitter_username}\n"
            f"📧 Campaign: {campaign_config['name']}\n"
            f"🔥 Warmup: {'Yes' if use_warmup else 'No'}\n"
            f"📊 Emails/day: {mails_per_day}\n\n"
            f"Start campaign?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Store mail per day in session
        self.user_sessions[user_id]['mails_per_day'] = mails_per_day

        return WAITING_SETTINGS_CONFIRM

    async def confirm_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and start the campaign"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if query.data == "cancel_start":
            await query.edit_message_text("❌ Campaign cancelled")
            del self.user_sessions[user_id]
            return ConversationHandler.END

        session = self.user_sessions[user_id]

        # Start campaign
        result = self.campaign_manager.start_campaign(
            campaign_id=session['campaign_id'],
            twitter_username=session['twitter_username'],
            use_warmup_checkpoint=session['use_warmup_checkpoint'],
            mails_per_day=session['mails_per_day']
        )

        if result['success']:
            await query.edit_message_text(
                f"✅ {result['message']}\n\n"
                f"Campaign is now running. Use /status to monitor progress."
            )
        else:
            await query.edit_message_text(f"❌ Error: {result['message']}")

        del self.user_sessions[user_id]
        return ConversationHandler.END

    # ========================================
    # EMAIL MANAGEMENT (NEW)
    # ========================================

    async def add_emails(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_emails command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return ConversationHandler.END

        # Show campaign selection
        campaigns = self.campaign_manager.get_campaigns()
        keyboard = []
        for campaign_id in campaigns:
            campaign_config = self.campaign_manager.get_campaign_config(campaign_id)
            keyboard.append([
                InlineKeyboardButton(
                    campaign_config['name'],
                    callback_data=f"addemail_{campaign_id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📧 **Add Emails**\n\nSelect campaign:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_EMAIL_CAMPAIGN

    async def receive_email_campaign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive campaign for email addition"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        campaign_id = query.data.replace("addemail_", "")

        self.user_sessions[user_id] = {'campaign_id': campaign_id}

        # Ask for email type
        keyboard = [
            [InlineKeyboardButton("🔥 Warmup Emails", callback_data="emailtype_warmup")],
            [InlineKeyboardButton("✓ Checkpoint Emails", callback_data="emailtype_checkpoint")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📋 Campaign: **{campaign_id}**\n\nSelect email type:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_EMAIL_TYPE

    async def receive_email_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive email type selection"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        email_type = query.data.replace("emailtype_", "")

        self.user_sessions[user_id]['email_type'] = email_type

        await query.edit_message_text(
            f"📝 **Add {email_type.title()} Emails**\n\n"
            f"Send emails in one of these formats:\n\n"
            f"**Comma-separated:**\n"
            f"`email1@test.com, email2@test.com, email3@test.com`\n\n"
            f"**Line-separated:**\n"
            f"`email1@test.com`\n"
            f"`email2@test.com`\n"
            f"`email3@test.com`\n\n"
            f"**With names:**\n"
            f"`John <john@test.com>, Jane <jane@test.com>`\n\n"
            f"Send as many as you want!",
            parse_mode='Markdown'
        )
        return WAITING_EMAIL_INPUT

    async def receive_email_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and process email input"""
        user_id = update.effective_user.id
        email_text = update.message.text

        session = self.user_sessions[user_id]
        campaign_id = session['campaign_id']
        email_type = session['email_type']

        # Add emails
        if email_type == 'warmup':
            result = self.email_manager.add_warmup_emails(campaign_id, email_text)
        else:
            result = self.email_manager.add_checkpoint_emails(campaign_id, email_text)

        if result['success']:
            await update.message.reply_text(
                f"✅ {result['message']}\n"
                f"📊 Total {email_type} emails: **{result['total']}**",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Error: {result['message']}")

        del self.user_sessions[user_id]
        return ConversationHandler.END

    async def view_emails(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /view_emails command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return ConversationHandler.END

        # Show campaign selection
        campaigns = self.campaign_manager.get_campaigns()
        keyboard = []
        for campaign_id in campaigns:
            campaign_config = self.campaign_manager.get_campaign_config(campaign_id)
            keyboard.append([
                InlineKeyboardButton(
                    campaign_config['name'],
                    callback_data=f"viewemail_{campaign_id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📋 **View Emails**\n\nSelect campaign:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_VIEW_CAMPAIGN

    async def receive_view_campaign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive campaign for viewing emails"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        campaign_id = query.data.replace("viewemail_", "")

        self.user_sessions[user_id] = {'campaign_id': campaign_id}

        # Ask for email type
        keyboard = [
            [InlineKeyboardButton("🔥 Warmup Emails", callback_data="viewtype_warmup")],
            [InlineKeyboardButton("✓ Checkpoint Emails", callback_data="viewtype_checkpoint")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📋 Campaign: **{campaign_id}**\n\nSelect email type:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_VIEW_TYPE

    async def receive_view_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive email type and show emails"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        email_type = query.data.replace("viewtype_", "")

        session = self.user_sessions[user_id]
        campaign_id = session['campaign_id']

        # Get emails
        if email_type == 'warmup':
            emails = self.email_manager.list_warmup_emails(campaign_id)
        else:
            emails = self.email_manager.list_checkpoint_emails(campaign_id)

        if not emails:
            await query.edit_message_text(
                f"ℹ️ No {email_type} emails found for campaign **{campaign_id}**",
                parse_mode='Markdown'
            )
        else:
            # Format email list
            email_list = f"📧 **{email_type.title()} Emails** ({len(emails)} total)\n\n"
            for idx, email in enumerate(emails[:20], 1):  # Show first 20
                email_list += f"{idx}. {email['email']} ({email['name']})\n"

            if len(emails) > 20:
                email_list += f"\n... and {len(emails) - 20} more"

            await query.edit_message_text(email_list, parse_mode='Markdown')

        del self.user_sessions[user_id]
        return ConversationHandler.END

    async def stop_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_process command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return ConversationHandler.END

        campaigns = self.campaign_manager.get_campaigns()
        active_campaigns = []

        for campaign_id in campaigns:
            status = self.campaign_manager.get_campaign_status(campaign_id)
            if status['is_running']:
                active_campaigns.append(campaign_id)

        if not active_campaigns:
            await update.message.reply_text("ℹ️ No active campaigns")
            return ConversationHandler.END

        keyboard = []
        for campaign_id in active_campaigns:
            keyboard.append([
                InlineKeyboardButton(
                    f"Stop: {campaign_id}",
                    callback_data=f"stop_{campaign_id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⏸️ Select campaign to stop:",
            reply_markup=reply_markup
        )
        return WAITING_STOP_CONFIRM

    async def confirm_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm stop campaign"""
        query = update.callback_query
        await query.answer()

        campaign_id = query.data.replace("stop_", "")
        result = self.campaign_manager.stop_campaign(campaign_id)

        if result['success']:
            await query.edit_message_text(f"⏸️ {result['message']}")
        else:
            await query.edit_message_text(f"❌ Error: {result['message']}")

        return ConversationHandler.END

    async def continue_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /continue_process command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return ConversationHandler.END

        campaigns = self.campaign_manager.get_campaigns()
        paused_campaigns = []

        for campaign_id in campaigns:
            status = self.campaign_manager.get_campaign_status(campaign_id)
            if status['status'] in ['paused', 'stopped'] and not status['is_running']:
                paused_campaigns.append(campaign_id)

        if not paused_campaigns:
            await update.message.reply_text("ℹ️ No paused campaigns")
            return ConversationHandler.END

        keyboard = []
        for campaign_id in paused_campaigns:
            status = self.campaign_manager.get_campaign_status(campaign_id)
            keyboard.append([
                InlineKeyboardButton(
                    f"Continue: {campaign_id} ({status['total_sent']} sent)",
                    callback_data=f"continue_{campaign_id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "▶️ Select campaign to continue:",
            reply_markup=reply_markup
        )
        return WAITING_CONTINUE_CONFIRM

    async def confirm_continue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm continue campaign"""
        query = update.callback_query
        await query.answer()

        campaign_id = query.data.replace("continue_", "")
        result = self.campaign_manager.continue_campaign(campaign_id)

        if result['success']:
            await query.edit_message_text(f"▶️ {result['message']}")
        else:
            await query.edit_message_text(f"❌ Error: {result['message']}")

        return ConversationHandler.END

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized")
            return

        campaigns = self.campaign_manager.get_campaigns()
        status_text = "📊 **Campaign Status**\n\n"

        for campaign_id in campaigns:
            status = self.campaign_manager.get_campaign_status(campaign_id)
            status_emoji = "🟢" if status['is_running'] else "🔴"

            status_text += f"{status_emoji} **{campaign_id}**\n"
            status_text += f"  Status: {status['status']}\n"
            if status.get('twitter_username'):
                status_text += f"  Twitter: @{status['twitter_username']}\n"
            status_text += f"  Sent today: {status['emails_sent_today']}/{status['settings']['mails_per_day']}\n"
            status_text += f"  Total sent: {status['total_sent']}\n"
            status_text += f"  Total failed: {status['total_failed']}\n"
            status_text += "\n"

        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        await update.message.reply_text("❌ Operation cancelled")
        return ConversationHandler.END

    def run(self):
        """Run the bot"""
        app = Application.builder().token(self.bot_token).build()

        # Start process conversation
        start_conv = ConversationHandler(
            entry_points=[CommandHandler("start_process", self.start_process)],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_username)],
                WAITING_CAMPAIGN: [CallbackQueryHandler(self.receive_campaign, pattern="^campaign_")],
                WAITING_SETTINGS_CONFIRM: [
                    CallbackQueryHandler(self.receive_warmup_setting, pattern="^warmup_"),
                    CallbackQueryHandler(self.confirm_start, pattern="^(confirm_start|cancel_start)$")
                ],
                WAITING_MAIL_PER_DAY: [CallbackQueryHandler(self.receive_mail_per_day, pattern="^mpd_")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Stop process conversation
        stop_conv = ConversationHandler(
            entry_points=[CommandHandler("stop_process", self.stop_process)],
            states={
                WAITING_STOP_CONFIRM: [CallbackQueryHandler(self.confirm_stop, pattern="^stop_")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Continue process conversation
        continue_conv = ConversationHandler(
            entry_points=[CommandHandler("continue_process", self.continue_process)],
            states={
                WAITING_CONTINUE_CONFIRM: [CallbackQueryHandler(self.confirm_continue, pattern="^continue_")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Add emails conversation
        add_emails_conv = ConversationHandler(
            entry_points=[CommandHandler("add_emails", self.add_emails)],
            states={
                WAITING_EMAIL_CAMPAIGN: [CallbackQueryHandler(self.receive_email_campaign, pattern="^addemail_")],
                WAITING_EMAIL_TYPE: [CallbackQueryHandler(self.receive_email_type, pattern="^emailtype_")],
                WAITING_EMAIL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_email_input)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # View emails conversation
        view_emails_conv = ConversationHandler(
            entry_points=[CommandHandler("view_emails", self.view_emails)],
            states={
                WAITING_VIEW_CAMPAIGN: [CallbackQueryHandler(self.receive_view_campaign, pattern="^viewemail_")],
                WAITING_VIEW_TYPE: [CallbackQueryHandler(self.receive_view_type, pattern="^viewtype_")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Add handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(start_conv)
        app.add_handler(stop_conv)
        app.add_handler(continue_conv)
        app.add_handler(add_emails_conv)
        app.add_handler(view_emails_conv)
        app.add_handler(CommandHandler("status", self.status))

        print("🤖 Extended Telegram bot started...")
        app.run_polling()


if __name__ == "__main__":
    bot = ExtendedTelegramBot()
    bot.run()
