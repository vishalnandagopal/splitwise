"""
File containing the classes used in my splitwise implementation.

### Classes
1. Member
2. SplitwiseGroup
3. DebtList
4. GroupDebtList
5. TransactionLog

### Convention

Person has to get money = +ve debt for person who has to get, -ve for person who has to give. We add to the debt to the A if he pays for B, and subtract from the debt of B. Add to a[b], and subtract from b[a] simultaneously.

The icecream module is used for debugging, and it runs the debug statements if an env variable "DEBUG" is set to true.
"""
from __future__ import annotations

import logging
from os import getenv
from typing import Optional
from uuid import UUID, uuid4

from colorama import Fore
from dotenv import load_dotenv
from icecream import ic  # type: ignore

#

load_dotenv("splitwise.env")
logger = logging.getLogger("splitwise")
logging.basicConfig(
    format="%(asctime)s %(message)s",
    filename="splitwise.log",
    encoding="utf-8",
    level=logging.DEBUG,
)


env_default_currency_prefix: str | None = getenv("PREFERRED_CURRENCY")

default_currency_prefix: str

if env_default_currency_prefix:
    default_currency_prefix = env_default_currency_prefix
else:
    default_currency_prefix = "₹"


def generate_uniq_id(type: str = "transaction") -> str:
    if type.casefold() == "member":
        return "mb-" + str(uuid4())
    elif type.casefold() == "group":
        return "gr-" + str(uuid4())
    elif type.casefold() == "transaction":
        return "tr-" + str(uuid4())
    elif type.casefold() == "dlist":
        return "dl-" + str(uuid4())
    elif type.casefold() == "group-dlist":
        return "gd-" + str(uuid4())
    return "o-" + str(uuid4())


def log_and_print(msg: str, level: str = "warn") -> None:
    log_to_file: Optional[str] = getenv("KEEP_A_LOG")
    print(msg)
    if str(log_to_file).casefold() not in ("false", "no", "none"):
        if level == "warn":
            logger.warning(msg)
        elif level == "critical":
            logger.critical(msg)
        elif level == "info":
            logger.info(msg)
        else:
            logger.debug(msg)


class TransactionLog:
    """
    Any transaction can be recorded using this class. Every payment is an object of the TransactionLog, and it has the following attributes.

    `debited_from`: An object of the `Member` class, who gave the money.
    `credited_to`: An object of the `member` class, who received the money.
    `amount`: The amount that was paid.
    `currency_prefix`: The currency the transaction was made in.
    If the Transaction was made in a group of the type `SplitwiseGroup`, these additional attributes can be provided
    `group_name`
    """

    def __init__(
        self,
        debited_from: Member,
        credited_to: Member,
        amount: int = 0,
        currency_prefix: str = default_currency_prefix,
        group: Optional[SplitwiseGroup] = None,
        previous_transaction: Optional[TransactionLog] = None,
    ):
        self.debited_from: Member = debited_from
        self.credited_to: Member = credited_to
        self.amount: int = amount
        self.currency: str = currency_prefix
        if group:
            self.group_name: Optional[str] = group.name
            self.group_id: Optional[str] = group.uniq_id_group
        else:
            self.group_name, self.group_id = None, None
        self.prev: Optional[TransactionLog] = previous_transaction
        self.next: Optional[TransactionLog] = None

        self.unique_id: str = generate_uniq_id("transaction")

    def __str__(self) -> str:
        string_repr = (
            f'{self.debited_from.name} paid {self.currency}{self.amount} to {self.credited_to.name} in the group "{self.group_name}."'
            if self.group_name
            else f"{self.debited_from.name} paid {self.currency}{self.amount} to {self.credited_to.name}"
        )
        if self.prev:
            string_repr += f" Prev transaction is {self.prev.unique_id}."
        if self.next:
            string_repr += f" Next transaction is {self.next.unique_id}."
        return string_repr

    def __repr__(self) -> str:
        return str(self)

    def recursive_print(self) -> None:
        print(
            f"{self.debited_from.name} paid {self.currency}{self.amount} to {self.credited_to.name}",
            end="  ->  ",
        )
        if self.next and self.next != self:
            self.next.recursive_print()


class DebtList:
    def __init__(
        self,
        name: str,
        members: tuple[Member, ...] = (),
        default_amount: int = 0,
        preferred_currency_prefix: str = default_currency_prefix,
    ):
        self.name: str = name

        self.debt_list: dict[Member, int] = dict()
        self.uniq_id_group: str = generate_uniq_id(type="dlist")
        self.preferred_currency_prefix_debt_list: str = preferred_currency_prefix

        for member in members:
            self.debt_list[member] = default_amount

    def update(self, person_self_paid_to: Member, amount: int = 0):
        """
        This value will be set as default if the self Member object does not have the person he owes money to in his debt list. If self pays for someone else, the debt in his debt list will increase positively.

        Eg: Debtlist[B]=600 means B owes 600.
        """
        if person_self_paid_to in self.debt_list:
            self.debt_list[person_self_paid_to] += amount
        else:
            self.debt_list[person_self_paid_to] = amount

    def __str__(self) -> str:
        """String representation of a debt list, useful for printing it."""
        if not self.debt_list:
            return f"{self.name} doesn't have a debt list."
        string_repr: str = ""
        net_debt: int = 0
        string_repr += f"Debt list for {self.name} is:"
        for member in self.debt_list:
            if self.debt_list[member] > 0:
                net_debt += self.debt_list[member]
                string_repr += f"\n     {Fore.GREEN}++ {Fore.RESET}{self.debt_list[member]} from {member.name}"
            elif self.debt_list[member] < 0:
                net_debt += self.debt_list[member]
                string_repr += f"\n     {Fore.RED}-- {Fore.RESET}{-self.debt_list[member]} to {member.name}"
        if net_debt > 0:
            string_repr += f"\n   {self.name} gets back {net_debt} in total."
        elif net_debt < 0:
            string_repr += f"\n   {self.name} has to pay {-net_debt} in total."
        else:
            string_repr += f"\n   {self.name} has a net debt is 0. Congrats!"
        return string_repr


class GroupDebtList:
    def __init__(
        self,
        name: str,
        members: list[Member] | tuple[Member] = [],
        default_amount: int = 0,
        preferred_currency_prefix: str = default_currency_prefix,
    ):
        self.name: str = name
        self.debt_list: dict[Member, int] = dict()
        self.amount_in_group: int = default_amount
        for member in members:
            self.debt_list[member] = default_amount
        self.group_transactions: list[TransactionLog] = []
        self.uniq_id_group: str = generate_uniq_id(type="group-dlist")
        self.preferred_currency_prefix: str = preferred_currency_prefix

    def update(
        self, person_who_paid: Member, person_who_got_the_money: Member, amount: int = 0
    ):
        self.amount_in_group += amount
        self.debt_list.update()
        self.debt_list[person_who_paid] += amount
        self.debt_list[person_who_got_the_money] -= amount

    def get_dicts_of_debts(self) -> tuple[dict[Member, int], ...]:
        owes_money: dict[Member, int] = {
            person: self.debt_list[person]
            for person in self.debt_list
            if self.debt_list[person] < 0
        }
        gets_money: dict[Member, int] = {
            person: self.debt_list[person]
            for person in self.debt_list
            if self.debt_list[person] > 0
        }
        no_debt: dict[Member, int] = {
            person: self.debt_list[person]
            for person in self.debt_list
            if self.debt_list[person] == 0
        }
        return (owes_money, gets_money, no_debt)

    def calculate_settlements(self) -> list[TransactionLog]:
        if self.debt_list:
            (owes_money, gets_money, no_debt) = self.get_dicts_of_debts()

            max_owed: int = min(owes_money.values())
            max_owed_person: Member = [
                person for person in owes_money if owes_money[person] == max_owed
            ][0]

            max_gets: int = max(gets_money.values())
            max_gets_person: Member = [
                person for person in gets_money if gets_money[person] == max_gets
            ][0]
            transactions_needed_to_settle: list[TransactionLog] = []

            while max_owed < 0 and max_gets > 0:
                # When comparing max_gets and max_owed to decide how to redistribute the debts, you need to compare
                if max_gets >= -max_owed:
                    amount = -max_owed
                else:
                    amount = max_gets

                transactions_needed_to_settle.append(
                    TransactionLog(max_owed_person, max_gets_person, amount)
                )
                owes_money[max_owed_person] += amount
                gets_money[max_gets_person] -= amount

                max_owed = min(owes_money.values())
                max_owed_person = [
                    person for person in owes_money if owes_money[person] == max_owed
                ][0]

                max_gets = max(gets_money.values())
                max_gets_person = [
                    person for person in gets_money if gets_money[person] == max_gets
                ][0]
                if str(getenv("DEBUG")).casefold() not in ("false", "no", "none", ""):
                    ic(
                        owes_money,
                        gets_money,
                        max_gets,
                        max_owed,
                    )
            return transactions_needed_to_settle

        else:
            log_and_print(f"{self.name} group debt list does not have any members")
            return []


class Member:
    def __init__(
        self, name: str, preferred_currency_prefix: str = default_currency_prefix
    ):
        self.name: str = name
        self.uniq_id_member: str = generate_uniq_id(type="member")
        self.preferred_currency_prefix_member: str = preferred_currency_prefix
        self.groups: set[SplitwiseGroup] = set()
        self.non_group_debts: DebtList = DebtList(
            self.name,
        )
        self.first_non_group_transaction: Optional[TransactionLog] = None
        self.last_non_group_transaction: TransactionLog

    def non_group_transaction(
        self,
        person_who_was_given_money: Member,
        amount: int = 0,
        changed_in_other_person_object: bool = False,
    ):
        self.non_group_debts.update(person_who_was_given_money, amount)
        if not self.first_non_group_transaction:
            self.first_non_group_transaction = TransactionLog(
                self,
                person_who_was_given_money,
                amount,
                self.preferred_currency_prefix_member,
                None,
            )
            self.last_non_group_transaction = self.first_non_group_transaction
        _ = TransactionLog(
            self,
            person_who_was_given_money,
            amount,
            self.preferred_currency_prefix_member,
            previous_transaction=self.last_non_group_transaction,
        )

        self.last_non_group_transaction.next = _
        self.last_non_group_transaction = _

        if not changed_in_other_person_object:
            person_who_was_given_money.non_group_transaction(self, -amount, True)

    def __str__(self) -> str:
        return f"Name: {self.name}, ID: {self.uniq_id_member}."

    def __repr__(self) -> str:
        return f"Name: {self.name}"


class SplitwiseGroup:
    def __init__(self, name: str, members: list[Member] | tuple[Member, ...] = []):
        self.name: str = name
        self.uniq_id_group: str = generate_uniq_id(type="group")
        self.members: list[Member] = list(members)
        self.group_debts: GroupDebtList = GroupDebtList(self.name, self.members)
        for member in self.members:
            member.groups.add(self)
        self.first_non_group_transaction: Optional[TransactionLog] = None
        self.last_non_group_transaction: TransactionLog
        self.determine_currency_prefix()

    def determine_currency_prefix(self):
        preferred_currencies = [
            member.preferred_currency_prefix_member for member in self.members
        ]
        if preferred_currencies:
            self.preferred_currency_prefix_group = max(preferred_currencies)
        else:
            self.preferred_currency_prefix_group = default_currency_prefix

    def add_member(self, person: Member | list[Member] | tuple[Member, ...]):
        if isinstance(person, Member):
            self.members.append(person)
        elif isinstance(person, (list, tuple)):
            self.members = self.members + list(person)
        else:
            log_and_print(
                "Can add only members from a list, tuple when given a single Member object."
            )

    def transaction(
        self,
        member_who_gave_money: Member,
        member_who_received_money: Member,
        amount: int,
    ) -> bool:
        if not self.first_non_group_transaction:
            self.first_non_group_transaction = TransactionLog(
                member_who_gave_money,
                member_who_received_money,
                amount,
                self.preferred_currency_prefix_group,
                self,
                None,
            )
            self.last_non_group_transaction = self.first_non_group_transaction
        _ = TransactionLog(
            member_who_gave_money,
            member_who_received_money,
            amount,
            self.preferred_currency_prefix_group,
            self,
            self.last_non_group_transaction,
        )

        self.last_non_group_transaction.next = _
        self.last_non_group_transaction = _
        if (
            member_who_gave_money in self.members
            and member_who_received_money in self.members
        ):
            self.group_debts.update(
                member_who_gave_money, member_who_received_money, amount
            )
            return True
        else:
            non_member = (
                member_who_received_money
                if member_who_received_money not in self.members
                else member_who_gave_money
            )
            other_member = member_who_gave_money if non_member == member_who_received_money else member_who_received_money
            log_and_print(
                f'{non_member.name} is not in the spltiwise group. Please make a transaction between {non_member.name} and {other_member.name} outside of this group "{self.name}", or add {non_member.name} to this group.'
            )
            return False

    def print_settlements(self) -> None:
        transactions_needed_to_settle: list[str] = []
        settlements: list[TransactionLog] = self.group_debts.calculate_settlements()
        print(f'The settlements to clear all debts in the group "{self.name}" are:')
        for transaction in settlements:
            print(
                f"    {transaction.debited_from.name} can pay {transaction.currency}{transaction.amount} to {transaction.credited_to.name}"
            )
