from accounts.models import ExchangeUserConfigs


class CreateUserConfigMixin(object):
    def has_user_accounts_config(self):
        configs = ExchangeUserConfigs.objects.filter(user=self.user)
        if configs.exists():
            return configs
        return False

    def create_user_accounts_config(self):
        configs = ExchangeUserConfigs.objects.create(user=self.user)
        return configs

    def get_user_accounts_config(self):
        configs = ExchangeUserConfigs.objects.get(user=self.user)
        return configs

    def get_user_exchange_config(self, exchange_name):
        try:
            user_configs = ExchangeUserConfigs.objects.get(user=self.user)
            config = user_configs.configs.get(exchange__name=exchange_name)
        except Exception:
            config = None
        return config
