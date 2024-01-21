class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Replace the placeholders with actual values from your result
your_user = "postgres"
your_password = "admin"
your_database = "Recipies"

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{your_user}:{your_password}@localhost/{your_database}'
    )

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{your_user}:{your_password}@localhost/{your_database}'
    )

# Choose the configuration class based on your environment (development or production)
config_env = "development"  # Change this to "production" if needed

if config_env == "production":
    app_config = ProductionConfig
else:
    app_config = DevelopmentConfig
