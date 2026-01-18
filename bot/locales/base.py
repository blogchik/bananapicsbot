"""Base translation utilities."""

from enum import Enum
from typing import Callable

from .manager import LocaleManager


class TranslationKey(str, Enum):
    """Translation keys enum for type safety."""
    
    # Common
    WELCOME = "welcome"
    WELCOME_BACK = "welcome_back"
    START_INFO = "start_info"
    ERROR_GENERIC = "error_generic"
    ERROR_CONNECTION = "error_connection"
    BACK = "back"
    HOME = "home"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    YES = "yes"
    NO = "no"
    LOADING = "loading"
    
    # Profile
    PROFILE_TITLE = "profile_title"
    PROFILE_INFO = "profile_info"
    PROFILE_NAME = "profile_name"
    PROFILE_USERNAME = "profile_username"
    PROFILE_TELEGRAM_ID = "profile_telegram_id"
    PROFILE_ID_LABEL = "profile_id_label"
    PROFILE_BALANCE = "profile_balance"
    PROFILE_GENERATIONS_ESTIMATE = "profile_generations_estimate"
    PROFILE_TRIAL = "profile_trial"
    PROFILE_TRIAL_AVAILABLE = "profile_trial_available"
    PROFILE_TRIAL_UNAVAILABLE = "profile_trial_unavailable"
    PROFILE_TRIAL_USED = "profile_trial_used"
    
    # Referral
    REFERRAL_TITLE = "referral_title"
    REFERRAL_INFO = "referral_info"
    REFERRAL_LINK = "referral_link"
    REFERRAL_COUNT = "referral_count"
    REFERRAL_BONUS = "referral_bonus"
    REFERRAL_DESCRIPTION = "referral_description"
    REFERRAL_BONUS_TOTAL = "referral_bonus_total"
    REFERRAL_NEW_APPLIED = "referral_new_applied"
    
    # Errors
    ERROR_USER_NOT_FOUND = "error_user_not_found"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    USER_NOT_FOUND = "user_not_found"
    MODEL_NOT_FOUND = "model_not_found"
    
    # Menu buttons
    BTN_PROFILE = "btn_profile"
    BTN_TOPUP = "btn_topup"
    BTN_REFERRAL = "btn_referral"
    BTN_SETTINGS = "btn_settings"
    BTN_HELP = "btn_help"
    BTN_LANGUAGE = "btn_language"
    BTN_START = "btn_start"
    BTN_GENERATION = "btn_generation"
    BTN_WATERMARK = "btn_watermark"
    
    # Command descriptions
    CMD_HOME = "cmd_home"
    CMD_PROFILE = "cmd_profile"
    CMD_TOPUP = "cmd_topup"
    CMD_REFERRAL = "cmd_referral"

    # Home menus
    GEN_MENU_TEXT = "gen_menu_text"
    WM_MENU_TEXT = "wm_menu_text"
    
    # Generation
    GEN_SETTINGS_TITLE = "gen_settings_title"
    GEN_SETTINGS_TITLE_T2I = "gen_settings_title_t2i"
    GEN_SETTINGS_TITLE_I2I = "gen_settings_title_i2i"
    GEN_PROMPT = "gen_prompt"
    GEN_MODEL = "gen_model"
    GEN_SIZE = "gen_size"
    GEN_ASPECT_RATIO = "gen_aspect_ratio"
    GEN_RESOLUTION = "gen_resolution"
    GEN_QUALITY = "gen_quality"
    GEN_INPUT_FIDELITY = "gen_input_fidelity"
    GEN_DEFAULT = "gen_default"
    GEN_START_BUTTON = "gen_start_button"
    GEN_IN_QUEUE = "gen_in_queue"
    GEN_PROCESSING = "gen_processing"
    GEN_COMPLETED = "gen_completed"
    GEN_FAILED = "gen_failed"
    GEN_RESULT_CAPTION = "gen_result_caption"
    GEN_ACTIVE_EXISTS = "gen_active_exists"
    GEN_PROMPT_REQUIRED = "gen_prompt_required"
    GEN_PROMPT_WITH_IMAGE = "gen_prompt_with_image"
    GEN_MAX_REFERENCES = "gen_max_references"
    GEN_UPLOAD_ERROR = "gen_upload_error"
    GEN_TIMEOUT = "gen_timeout"
    GEN_STATUS_CHECK_ERROR = "gen_status_check_error"
    GEN_ACCEPTED = "gen_accepted"
    GEN_CONFLICT = "gen_conflict"
    GEN_ERROR = "gen_error"
    GEN_SEND_ERROR = "gen_send_error"
    GEN_STATUS = "gen_status"
    GEN_TRIAL_USED = "gen_trial_used"
    GEN_PRICE = "gen_price"
    GEN_RETRY = "gen_retry"
    GEN_PROMPT_NOT_FOUND = "gen_prompt_not_found"
    GEN_MODEL_FETCH_ERROR = "gen_model_fetch_error"
    GEN_MODEL_NOT_FOUND_ERROR = "gen_model_not_found_error"
    GEN_SIZE_NOT_AVAILABLE = "gen_size_not_available"
    GEN_ASPECT_NOT_AVAILABLE = "gen_aspect_not_available"
    GEN_RESOLUTION_NOT_AVAILABLE = "gen_resolution_not_available"
    GEN_IMAGE_ONLY = "gen_image_only"
    GEN_INSUFFICIENT_BALANCE = "gen_insufficient_balance"
    GEN_STATUS_CHECK_TEMP_ERROR = "gen_status_check_temp_error"
    GEN_ERROR_GENERIC = "gen_error_generic"
    GEN_PROVIDER_UNAVAILABLE = "gen_provider_unavailable"
    GEN_STATUS_LABEL_QUEUE = "gen_status_label_queue"
    GEN_STATUS_LABEL_PROCESSING = "gen_status_label_processing"
    GEN_MODEL_MENU_QUALITY = "gen_model_menu_quality"
    GEN_MODEL_MENU_DURATION = "gen_model_menu_duration"
    GEN_MODEL_MENU_SECONDS = "gen_model_menu_seconds"
    GEN_MODEL_MENU_MINUTES = "gen_model_menu_minutes"
    GEN_MODEL_MENU_PRICE = "gen_model_menu_price"
    GEN_MODEL_MENU_HINT = "gen_model_menu_hint"
    GEN_ASPECT_MENU_TITLE = "gen_aspect_menu_title"
    GEN_RESOLUTION_MENU_TITLE = "gen_resolution_menu_title"
    GEN_QUALITY_MENU_TITLE = "gen_quality_menu_title"
    GEN_INPUT_FIDELITY_MENU_TITLE = "gen_input_fidelity_menu_title"
    GEN_QUALITY_NOT_AVAILABLE = "gen_quality_not_available"
    GEN_INPUT_FIDELITY_NOT_AVAILABLE = "gen_input_fidelity_not_available"

    # Watermark tool
    WM_MENU_TITLE = "wm_menu_title"
    WM_REMOVE_BUTTON = "wm_remove_button"
    WM_PROCESSING = "wm_processing"
    WM_FAILED = "wm_failed"
    WM_SUCCESS = "wm_success"
    
    # Payments
    TOPUP_TITLE = "topup_title"
    TOPUP_DESCRIPTION = "topup_description"
    TOPUP_EXCHANGE_RATE = "topup_exchange_rate"
    TOPUP_SELECT_AMOUNT = "topup_select_amount"
    TOPUP_APPROX_GENERATIONS = "topup_approx_generations"
    TOPUP_PRESET_LABEL = "topup_preset_label"
    TOPUP_CUSTOM = "topup_custom"
    TOPUP_ENTER_AMOUNT = "topup_enter_amount"
    TOPUP_MIN_AMOUNT = "topup_min_amount"
    TOPUP_INVALID_AMOUNT = "topup_invalid_amount"
    TOPUP_INVOICE_DESCRIPTION = "topup_invoice_description"
    TOPUP_INVOICE_LABEL = "topup_invoice_label"
    TOPUP_CONFIRMATION = "topup_confirmation"
    TOPUP_SUCCESS = "topup_success"
    TOPUP_DISABLED = "topup_disabled"
    
    # Settings
    SETTINGS_TITLE = "settings_title"
    SETTINGS_LANGUAGE = "settings_language"
    SETTINGS_LANGUAGE_CHANGED = "settings_language_changed"
    
    # Admin
    ADMIN_PANEL_TITLE = "admin_panel_title"
    ADMIN_STATS = "admin_stats"
    ADMIN_USERS = "admin_users"
    ADMIN_ADD_CREDITS = "admin_add_credits"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_REFUND = "admin_refund"
    ADMIN_NOT_AUTHORIZED = "admin_not_authorized"
    
    # Admin - Stats
    ADMIN_STATS_TITLE = "admin_stats_title"
    ADMIN_STATS_USERS_TOTAL = "admin_stats_users_total"
    ADMIN_STATS_USERS_TODAY = "admin_stats_users_today"
    ADMIN_STATS_USERS_WEEK = "admin_stats_users_week"
    ADMIN_STATS_USERS_MONTH = "admin_stats_users_month"
    ADMIN_STATS_USERS_ACTIVE = "admin_stats_users_active"
    ADMIN_STATS_USERS_PAYING = "admin_stats_users_paying"
    ADMIN_STATS_GENS_TOTAL = "admin_stats_gens_total"
    ADMIN_STATS_GENS_TODAY = "admin_stats_gens_today"
    ADMIN_STATS_GENS_WEEK = "admin_stats_gens_week"
    ADMIN_STATS_GENS_COMPLETED = "admin_stats_gens_completed"
    ADMIN_STATS_GENS_FAILED = "admin_stats_gens_failed"
    ADMIN_STATS_CREDITS_SPENT = "admin_stats_credits_spent"
    ADMIN_STATS_BY_MODEL = "admin_stats_by_model"
    ADMIN_STATS_REVENUE_TOTAL = "admin_stats_revenue_total"
    ADMIN_STATS_REVENUE_TODAY = "admin_stats_revenue_today"
    ADMIN_STATS_REVENUE_WEEK = "admin_stats_revenue_week"
    ADMIN_STATS_REVENUE_MONTH = "admin_stats_revenue_month"
    ADMIN_STATS_PAYMENTS_COUNT = "admin_stats_payments_count"
    ADMIN_STATS_AVG_PAYMENT = "admin_stats_avg_payment"
    ADMIN_STATS_AVG_BALANCE = "admin_stats_avg_balance"
    ADMIN_STATS_TOTAL_BALANCE = "admin_stats_total_balance"
    ADMIN_USER_STATS_TITLE = "admin_user_stats_title"
    ADMIN_GEN_STATS_TITLE = "admin_gen_stats_title"
    ADMIN_REVENUE_STATS_TITLE = "admin_revenue_stats_title"
    
    # Admin - Users
    ADMIN_USERS_TITLE = "admin_users_title"
    ADMIN_USER_SEARCH_PROMPT = "admin_user_search_prompt"
    ADMIN_USER_SEARCH_EMPTY = "admin_user_search_empty"
    ADMIN_USER_NOT_FOUND = "admin_user_not_found"
    ADMIN_USER_SELECT = "admin_user_select"
    ADMIN_USER_PROFILE_TITLE = "admin_user_profile_title"
    ADMIN_USER_ID = "admin_user_id"
    ADMIN_USER_USERNAME = "admin_user_username"
    ADMIN_USER_NAME = "admin_user_name"
    ADMIN_USER_BALANCE = "admin_user_balance"
    ADMIN_USER_TRIAL = "admin_user_trial"
    ADMIN_USER_GENERATIONS = "admin_user_generations"
    ADMIN_USER_CREATED = "admin_user_created"
    ADMIN_USER_LAST_ACTIVE = "admin_user_last_active"
    ADMIN_USER_BANNED = "admin_user_banned"
    ADMIN_USER_BANNED_SUCCESS = "admin_user_banned_success"
    ADMIN_USER_UNBANNED_SUCCESS = "admin_user_unbanned_success"
    ADMIN_USERS_LIST_TITLE = "admin_users_list_title"
    ADMIN_USERS_EMPTY = "admin_users_empty"
    
    # Admin - Credits
    ADMIN_CREDITS_ENTER_AMOUNT = "admin_credits_enter_amount"
    ADMIN_CREDITS_INVALID_AMOUNT = "admin_credits_invalid_amount"
    ADMIN_CREDITS_ZERO_AMOUNT = "admin_credits_zero_amount"
    ADMIN_CREDITS_ENTER_REASON = "admin_credits_enter_reason"
    ADMIN_CREDITS_ADDED = "admin_credits_added"
    ADMIN_CREDITS_REMOVED = "admin_credits_removed"
    ADMIN_ACTION_CANCELLED = "admin_action_cancelled"
    
    # Admin - Refund
    ADMIN_REFUND_NO_GENERATIONS = "admin_refund_no_generations"
    ADMIN_REFUND_SELECT = "admin_refund_select"
    ADMIN_REFUND_SUCCESS = "admin_refund_success"
    
    # Admin - Broadcast
    ADMIN_BROADCAST_TITLE = "admin_broadcast_title"
    ADMIN_BROADCAST_ENTER_MESSAGE = "admin_broadcast_enter_message"
    ADMIN_BROADCAST_PREVIEW = "admin_broadcast_preview"
    ADMIN_BROADCAST_CONFIRM_PROMPT = "admin_broadcast_confirm_prompt"
    ADMIN_BROADCAST_STARTED = "admin_broadcast_started"
    ADMIN_BROADCAST_CANCELLED = "admin_broadcast_cancelled"
    ADMIN_BROADCAST_EMPTY = "admin_broadcast_empty"
    ADMIN_BROADCAST_HISTORY_TITLE = "admin_broadcast_history_title"
    ADMIN_BROADCAST_STATUS_TITLE = "admin_broadcast_status_title"
    ADMIN_BROADCAST_ID = "admin_broadcast_id"
    ADMIN_BROADCAST_STATUS = "admin_broadcast_status"
    ADMIN_BROADCAST_SENT = "admin_broadcast_sent"
    ADMIN_BROADCAST_FAILED = "admin_broadcast_failed"
    ADMIN_BROADCAST_PENDING = "admin_broadcast_pending"


def get_translator(language: str) -> Callable[[TranslationKey, dict | None], str]:
    """Get translator function for language."""
    manager = LocaleManager.get_instance()
    
    def translate(key: TranslationKey, params: dict | None = None) -> str:
        return manager.get(language, key.value, params)
    
    return translate


def get_text(
    key: TranslationKey,
    language: str = "uz",
    params: dict | None = None,
) -> str:
    """Get translated text."""
    manager = LocaleManager.get_instance()
    return manager.get(language, key.value, params)


async def set_user_language(user_id: int, language: str) -> None:
    """Set user language preference."""
    from core.container import get_container
    
    container = get_container()
    await container.redis_client.set_user_language(user_id, language)
