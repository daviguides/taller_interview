import re
import uuid
import unittest


class UsernameException(Exception):
    pass


class PaymentException(Exception):
    pass


class CreditCardException(Exception):
    pass


class Payment:
    def __init__(
        self,
        amount: float,
        actor: "User",
        target: "User",
        note: str
    ) -> None:
        self.id: str = str(uuid.uuid4())
        self.amount: float = float(amount)
        self.actor: "User" = actor
        self.target: "User" = target
        self.note: str = note

    def __str__(self) -> str:
        return (
            f"{self.actor.username} paid {self.target.username} "
            f"${self.amount:.2f} for {self.note}"
        )


class User:
    def __init__(
        self,
        username: str
    ) -> None:
        self.credit_card_number: str | None = None
        self.balance: float = 0.0
        self.friends: set["User"] = set()
        self.activity_feed: list[str] = []

        if self._is_valid_username(username=username):
            self.username: str = username
        else:
            raise UsernameException("Username not valid.")

    def retrieve_feed(self) -> list[str]:
        return self.activity_feed

    def add_friend(
        self,
        new_friend: "User"
    ) -> None:
        if new_friend not in self.friends:
            self.friends.add(new_friend)
            new_friend.friends.add(self)

            message: str = (
                f"{self.username} and {new_friend.username} are now friends."
            )
            self.activity_feed.append(message)
            new_friend.activity_feed.append(message)

    def add_to_balance(
        self,
        amount: float
    ) -> None:
        self.balance += float(amount)

    def add_credit_card(
        self,
        credit_card_number: str
    ) -> None:
        if self.credit_card_number is not None:
            raise CreditCardException("Only one credit card per user!")

        if self._is_valid_credit_card(credit_card_number=credit_card_number):
            self.credit_card_number = credit_card_number
        else:
            raise CreditCardException("Invalid credit card number.")

    def pay(
        self,
        target: "User",
        amount: float,
        note: str
    ) -> Payment:
        amount = float(amount)

        if self.username == target.username:
            raise PaymentException("User cannot pay themselves.")

        if amount <= 0.0:
            raise PaymentException("Amount must be a positive number.")

        if self.balance >= amount:
            return self.pay_with_balance(target=target, amount=amount, note=note)

        if self.credit_card_number:
            return self.pay_with_card(target=target, amount=amount, note=note)

        raise PaymentException("Insufficient funds and no credit card available.")

    def pay_with_balance(
        self,
        target: "User",
        amount: float,
        note: str
    ) -> Payment:
        self.balance -= amount
        payment: Payment = Payment(amount=amount, actor=self, target=target, note=note)
        target.add_to_balance(amount=amount)

        self.activity_feed.append(str(payment))
        target.activity_feed.append(str(payment))
        return payment

    def pay_with_card(
        self,
        target: "User",
        amount: float,
        note: str
    ) -> Payment:
        self._charge_credit_card(credit_card_number=self.credit_card_number)
        payment: Payment = Payment(amount=amount, actor=self, target=target, note=note)

        if target != self:
            target.add_to_balance(amount=amount)

        self.activity_feed.append(str(payment))
        target.activity_feed.append(str(payment))
        return payment

    def _is_valid_credit_card(
        self,
        credit_card_number: str
    ) -> bool:
        return credit_card_number in {"4111111111111111", "4242424242424242"}

    def _is_valid_username(
        self,
        username: str
    ) -> bool:
        return bool(re.match(r"^[A-Za-z0-9_\\-]{4,15}$", username))

    def _charge_credit_card(
        self,
        credit_card_number: str
    ) -> None:
        pass  # Simulates credit card processing


class MiniVenmo:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def create_user(
        self,
        username: str,
        balance: float,
        credit_card_number: str | None = None
    ) -> User:
        if username in self.users:
            raise UsernameException("Username already taken.")

        user: User = User(username=username)
        user.add_to_balance(amount=balance)

        if credit_card_number:
            user.add_credit_card(credit_card_number=credit_card_number)

        self.users[username] = user
        return user

    def render_feed(
        self,
        feed: list[str]
    ) -> None:
        for event in feed:
            print(event)

    @classmethod
    def run(cls):
        venmo = cls()

        bobby = venmo.create_user("Bobby", 5.00, "4111111111111111")
        carol = venmo.create_user("Carol", 10.00, "4242424242424242")

        print('# Doing some payments')
        try:
            # should complete using balance
            bobby.pay(carol, 5.00, "Coffee")

            # should complete using card
            carol.pay(bobby, 15.00, "Lunch")
        except PaymentException as e:
            print(e)

        feed = bobby.retrieve_feed()
        venmo.render_feed(feed)

        print('\n# Adding a new friend')
        bobby.add_friend(carol)
        venmo.render_feed(feed)


# Unit Tests
class TestMiniVenmo(unittest.TestCase):
    def setUp(self) -> None:
        self.venmo: MiniVenmo = MiniVenmo()
        self.bobby: User = self.venmo.create_user(
            username="Bobby",
            balance=5.00,
            credit_card_number="4111111111111111"
        )
        self.carol: User = self.venmo.create_user(
            username="Carol",
            balance=10.00,
            credit_card_number="4242424242424242"
        )

    def test_create_user_that_already_exists(self) -> None:
        with self.assertRaises(UsernameException):
            self.venmo.create_user(
                username="Bobby",
                balance=10.00
            )

    def test_create_user_with_invalid_username(self) -> None:
        with self.assertRaises(UsernameException):
            self.venmo.create_user(
                username="Bobby$",
                balance=10.00
            )

    def test_payment_with_balance(self) -> None:
        self.bobby.pay(
            target=self.carol,
            amount=5.00,
            note="Coffee"
        )
        self.assertEqual(self.bobby.balance, 0.00)
        self.assertEqual(self.carol.balance, 15.00)

    def test_payment_with_card(self) -> None:
        self.carol.pay(
            target=self.bobby,
            amount=15.00,
            note="Lunch"
        )
        self.assertEqual(self.bobby.balance, 20.00)

    def test_feed(self) -> None:
        self.bobby.pay(
            target=self.carol,
            amount=5.00,
            note="Coffee"
        )

        self.carol.pay(
            target=self.bobby,
            amount=15.00,
            note="Lunch"
        )

        self.assertListEqual(
            [
                "Bobby paid Carol $5.00 for Coffee",
                "Carol paid Bobby $15.00 for Lunch",
            ],
            self.bobby.retrieve_feed()
        )

    def test_add_friend(self) -> None:
        self.bobby.add_friend(new_friend=self.carol)
        self.assertIn(self.carol, self.bobby.friends)
        self.assertIn(self.bobby, self.carol.friends)
        self.assertIn(
            "Bobby and Carol are now friends.",
            self.bobby.retrieve_feed()
        )

if __name__ == "__main__":
    unittest.main()