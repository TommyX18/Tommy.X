import os
from pathlib import Path
from datetime import timedelta

import environ


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT
# ============================================================

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")


# ============================================================
# SECURITY / CORE
# ============================================================

DEBUG = env.bool(
    "DEBUG",
    default=False,
)


SECRET_KEY = env(
    "SECRET_KEY",
    default="",
)


# Never allow an insecure fallback SECRET_KEY in production.
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-development-only-change-this"
    else:
        raise RuntimeError(
            "SECRET_KEY is missing. Set a strong SECRET_KEY in .env."
        )


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "127.0.0.1",
        "localhost",
    ],
)


RENDER_EXTERNAL_HOSTNAME = env(
    "RENDER_EXTERNAL_HOSTNAME",
    default=None,
)


if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(
        RENDER_EXTERNAL_HOSTNAME
    )


# ============================================================
# PRODUCTION DOMAIN
# ============================================================

# Put your production domains in .env:
#
# ALLOWED_HOSTS=tommyhub.in,www.tommyhub.in
#
# CSRF_TRUSTED_ORIGINS=https://tommyhub.in,https://www.tommyhub.in


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",

    # Local apps
    "core",
    "accounts",
    "products",
    "cart",
    "wishlist",
    "orders",
    "payments",
    "api",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [

    # Security MUST be near the top
    "django.middleware.security.SecurityMiddleware",

    # Static files
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS
    "corsheaders.middleware.CorsMiddleware",

    # Sessions
    "django.contrib.sessions.middleware.SessionMiddleware",

    # Common
    "django.middleware.common.CommonMiddleware",

    # CSRF
    "django.middleware.csrf.CsrfViewMiddleware",

    # Authentication
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Messages
    "django.contrib.messages.middleware.MessageMiddleware",

    # Clickjacking
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# CONTENT SECURITY POLICY
# ============================================================
#
# IMPORTANT:
# We start with REPORT-ONLY instead of enforcing CSP.
#
# Your project currently contains inline CSS/JS and external
# Bootstrap / Google Fonts / Razorpay resources.
#
# Report-only lets us discover violations without breaking
# the live storefront.
#
# After the site is tested, CSP can be enforced properly.
# ============================================================

if not DEBUG:

    MIDDLEWARE.insert(
        1,
        "django.middleware.csp.ContentSecurityPolicyMiddleware",
    )

    SECURE_CSP_REPORT_ONLY = {

        "default-src": [
            "'self'",
        ],

        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://checkout.razorpay.com",
        ],

        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
        ],

        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net",
            "data:",
        ],

        "img-src": [
            "'self'",
            "data:",
            "blob:",
            "https:",
        ],

        "connect-src": [
            "'self'",
            "https://api.razorpay.com",
        ],

        "frame-src": [
            "'self'",
            "https://checkout.razorpay.com",
        ],

        "object-src": [
            "'none'",
        ],

        "base-uri": [
            "'self'",
        ],

        "form-action": [
            "'self'",
            "https://checkout.razorpay.com",
        ],

        "frame-ancestors": [
            "'none'",
        ],
    }


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "tommyx_site.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

                "cart.context_processors.cart_wishlist",

                "products.context_processors.nav_categories",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "tommyx_site.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = env(
    "DATABASE_URL",
    default=None,
)


if DATABASE_URL:

    import dj_database_url

    DATABASES = {

        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
        )

    }

else:

    DB_ENGINE = env(
        "DB_ENGINE",
        default="sqlite",
    )


    if DB_ENGINE == "postgresql":

        DATABASES = {

            "default": {

                "ENGINE":
                    "django.db.backends.postgresql",

                "NAME":
                    env(
                        "DB_NAME",
                        default="tommyx_db",
                    ),

                "USER":
                    env(
                        "DB_USER",
                        default="postgres",
                    ),

                "PASSWORD":
                    env(
                        "DB_PASSWORD",
                        default="",
                    ),

                "HOST":
                    env(
                        "DB_HOST",
                        default="localhost",
                    ),

                "PORT":
                    env(
                        "DB_PORT",
                        default="5432",
                    ),

                "CONN_MAX_AGE":
                    600,
            }

        }

    else:

        DATABASES = {

            "default": {

                "ENGINE":
                    "django.db.backends.sqlite3",

                "NAME":
                    BASE_DIR / "db.sqlite3",

            }

        }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        },
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# STORAGE
# ============================================================

STORAGES = {

    "default": {

        "BACKEND":
            "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {

        "BACKEND":
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DEFAULT AUTO FIELD
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# AUTHENTICATION REDIRECTS
# ============================================================

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "accounts:profile"

LOGOUT_REDIRECT_URL = "core:home"


# ============================================================
# SESSION SECURITY
# ============================================================

SESSION_COOKIE_NAME = "tommyx_session"

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7

SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ============================================================
# CSRF SECURITY
# ============================================================

CSRF_COOKIE_NAME = "tommyx_csrf"

CSRF_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)


# ============================================================
# HTTPS / SSL SECURITY
# ============================================================

SECURE_SSL_REDIRECT = not DEBUG


# IMPORTANT:
# Your nginx reverse proxy must send:
#
# X-Forwarded-Proto: https
#
# Only enable this when nginx is configured correctly.

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if not DEBUG
    else None
)


# ============================================================
# HSTS
# ============================================================
#
# 1 year.
#
# Do NOT enable preload/includeSubDomains until you are certain
# every relevant subdomain is permanently HTTPS.
# ============================================================

SECURE_HSTS_SECONDS = (
    31536000
    if not DEBUG
    else 0
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = False

SECURE_HSTS_PRELOAD = False


# ============================================================
# SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

X_FRAME_OPTIONS = "DENY"


# ============================================================
# CORS
# ============================================================

if DEBUG:

    CORS_ALLOW_ALL_ORIGINS = True

else:

    CORS_ALLOW_ALL_ORIGINS = False

    CORS_ALLOWED_ORIGINS = env.list(
        "CORS_ALLOWED_ORIGINS",
        default=[],
    )


# ============================================================
# REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": (

        "rest_framework_simplejwt.authentication."
        "JWTAuthentication",

        "rest_framework.authentication."
        "SessionAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (

        "rest_framework.permissions."
        "IsAuthenticatedOrReadOnly",
    ),

    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination."
        "PageNumberPagination",

    "PAGE_SIZE": 12,

    "DEFAULT_FILTER_BACKENDS": (

        "django_filters.rest_framework."
        "DjangoFilterBackend",

        "rest_framework.filters."
        "SearchFilter",

        "rest_framework.filters."
        "OrderingFilter",
    ),

    # ========================================================
    # API RATE LIMITING
    # ========================================================

    "DEFAULT_THROTTLE_CLASSES": (

        "rest_framework.throttling."
        "AnonRateThrottle",

        "rest_framework.throttling."
        "UserRateThrottle",
    ),

    "DEFAULT_THROTTLE_RATES": {

        "anon": "60/min",

        "user": "300/min",
    },
}


# ============================================================
# SIMPLE JWT
# ============================================================

SIMPLE_JWT = {

    "ACCESS_TOKEN_LIFETIME":
        timedelta(
            minutes=env.int(
                "ACCESS_TOKEN_LIFETIME_MIN",
                default=30,
            )
        ),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(
            days=env.int(
                "REFRESH_TOKEN_LIFETIME_DAYS",
                default=7,
            )
        ),

    "ROTATE_REFRESH_TOKENS": True,

    "BLACKLIST_AFTER_ROTATION": True,

    "UPDATE_LAST_LOGIN": False,

    "AUTH_HEADER_TYPES": (
        "Bearer",
    ),

    "ALGORITHM": "HS256",

    "SIGNING_KEY": SECRET_KEY,

}


# ============================================================
# PAYMENTS — RAZORPAY
# ============================================================

RAZORPAY_KEY_ID = env(
    "RAZORPAY_KEY_ID",
    default="",
)

RAZORPAY_KEY_SECRET = env(
    "RAZORPAY_KEY_SECRET",
    default="",
)

RAZORPAY_WEBHOOK_SECRET = env(
    "RAZORPAY_WEBHOOK_SECRET",
    default="",
)


# ============================================================
# EMAIL
# ============================================================

EMAIL_HOST = env(
    "EMAIL_HOST",
    default="",
)

EMAIL_PORT = env.int(
    "EMAIL_PORT",
    default=587,
)

EMAIL_HOST_USER = env(
    "EMAIL_HOST_USER",
    default="",
)

EMAIL_HOST_PASSWORD = env(
    "EMAIL_HOST_PASSWORD",
    default="",
)

EMAIL_USE_TLS = True


if EMAIL_HOST:

    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )

else:

    if DEBUG:

        EMAIL_BACKEND = (
            "django.core.mail.backends.console.EmailBackend"
        )

    else:

        # Never silently use console email in production.
        raise RuntimeError(
            "EMAIL_HOST is missing in production."
        )


# ============================================================
# EMAIL SECURITY
# ============================================================

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="tommy.xattire@gmail.com",
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ============================================================
# TOMMY.X BRAND SETTINGS
# ============================================================

TOMMYX = {

    "BRAND_NAME":
        "TOMMY.X",

    "TAGLINE":
        "MEN",

    "EMAIL":
        env(
            "BRAND_EMAIL",
            default="tommy.xattire@gmail.com",
        ),

    "PHONE":
        env(
            "BRAND_PHONE",
            default="9751999225",
        ),
}


# ============================================================
# DEVELOPMENT / PRODUCTION CHECK
# ============================================================

if not DEBUG:

    # Production should never accidentally run with localhost
    # as the only allowed host.

    if not ALLOWED_HOSTS:

        raise RuntimeError(
            "ALLOWED_HOSTS must be configured in production."
        )