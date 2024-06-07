class StarlingData:
    """Get the latest data and update the states."""

    def __init__(self, account):
        """Init the starling data object."""
        self.available = False
        self.spaces = []
        self.starling_account = account

    def update_coordinated(self, _listening_idx):
        """Get the latest data from starling."""
        self.starling_account.update_balance_data()
        self.starling_account.update_savings_goal_data()
        self.available = True
        self.spaces = self.starling_account.savings_goals.items()
        result = self.spaces
        result['MASTER'] = self.starling_account
        return result
