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
    """
    Generate a random UUID (using UUID.uuid4()) and add a prefix to the string representation of the UUID based on what the UUID it is being generated for.

    Eg: If type is 'member', it adds the prefix 'mb' to the uuid and returns it.

    #### Parameters:
        `type`: 'transaction' | 'member' | 'group' | 'dlist' | 'group-dlist' | Any string
    """

    if type.casefold() == "transaction":
        return "tr-" + str(uuid4())
    elif type.casefold() == "member":
        return "mb-" + str(uuid4())
    elif type.casefold() == "group":
        return "gr-" + str(uuid4())
    elif type.casefold() == "dlist":
        return "dl-" + str(uuid4())
    elif type.casefold() == "group-dlist":
        return "gd-" + str(uuid4())
    return "ot-" + str(uuid4())


def log_and_print(msg: str, level: str = "warn") -> None:
    """
    This function can be used for printing an error message, as well as for logging it by passing the level to the level parameter.

    This function looks for the env variable `KEEP_A_LOG`, to check whether it should keep logs to the file.

    Printing always happens, irrespective of the value of `KEEP_A_LOG`.

    #### Parameters
        `msg` - The message to print/log.
        `
    """
    print(msg)

    log_to_file: Optional[str] = getenv("KEEP_A_LOG")

    if str(log_to_file).casefold() not in ("false", "no", "none"):
        if level == "warn":
            logger.warning(msg)
        elif level == "critical":
            logger.critical(msg)
        elif level == "info":
            logger.info(msg)
        else:
            logger.debug(msg)


def determine_currency_prefix(members: list[Member] | tuple[Member, ...]) -> str:
    """Calculates a currency prefix when given a list/tuple of `Member` objects, based on what the most frequent currency prefix is among all members is."""
    preferred_currencies: list[str] = [
        member.preferred_currency_prefix_member for member in members
    ]
    preferred_currency_prefix_group: str
    if preferred_currencies:
        preferred_currency_prefix_group = max(preferred_currencies)
    else:
        preferred_currency_prefix_group = default_currency_prefix
    return preferred_currency_prefix_group


class TransactionLog:
    """
    Any transaction can be recorded using this class. Every payment is an object of the TransactionLog, and it has the following attributes.
    #### Parameters
        `debited_from`: An object of the `Member` class, who gave the money.
        `credited_to`: An object of the `member` class, who received the money.
        `amount`: The amount that was paid.
        `currency_prefix`: The currency the transaction was made in.
    If the Transaction was made in a group of the type `SplitwiseGroup`, then a group argument can also be provided.
        `group` - The SplitwiseGroup object in which the transaction was made.
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
        return string_repr

    def __repr__(self) -> str:
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

    def recursive_print(self) -> None:
        # arrow = """   ----
        # |
        # |
        # ---
        # """
        arrow = """
            |
            ↓\n"""
        _ = self.next
        while _:
            print(
                str(_),
                end=arrow,
            )
            if _.next:
                _ = _.next
            else:
                break
        print(str(_))


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
            string_repr += f"\n   {self.name} owes {-net_debt} in total."
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
        self,
        name: str,
        preferred_currency_prefix: str = default_currency_prefix,
        upi_id: Optional[str] = None,
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
        self.upi_id: Optional[str] = upi_id

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
        self.preferred_currency_prefix_group = determine_currency_prefix(self.members)

    def add_member(self, person: Member | list[Member] | tuple[Member, ...]):
        """
        Add a `Member` or a list/tuple of `Member` objects as additional members to the `SplitwiseGroup`.
        #### Parameters:
            `person`: Member | list[Member] | tuple[Member, ...]
        """
        if isinstance(person, Member):
            self.members.append(person)
        elif isinstance(person, (list, tuple)):
            self.members += list(person)
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
        """
        Make a transaction in a `SplitwiseGroup`.
        #### Parameters
            `member_who_gave_money`: The person who lent the money.
            `member_who_received_money`: The person who received the money.
            `amount`: The amount involved in this transaction (preferably should be positive, but should also work with negative)
        """
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
            other_member = (
                member_who_gave_money
                if non_member == member_who_received_money
                else member_who_received_money
            )
            log_and_print(
                f'{non_member.name} is not in the spltiwise group. Please make a transaction between {non_member.name} and {other_member.name} outside of this group "{self.name}", or add {non_member.name} to this group.'
            )
            return False

    def print_settlements(self) -> None:
        """
        Prints a way to settle all debts by showing how members can pay each other, similar to a format used by Splitwise. It calculates money lent and owed by calling the `calculate_settlements()` function `self.group_debts`, a GroupDebtList, and then for each Transaction that is part of the possible settlement, it formats it in a way similar to users of Splitwise and then prints it.

        This function also contains a member_payments class that handles all formating and calculation while printing.
        """
        settlements: list[TransactionLog] = self.group_debts.calculate_settlements()

        class MemberPayments:
            """
            A class used to calculate and represent the settlements needed to be done in a group.
            #### Paremeters:
                `settlements`: A list of `TransactionLog` objects.
            """

            def __init__(self, settlements: list[TransactionLog]):
                if settlements:
                    self.members: list[Member] = [
                        transaction.credited_to for transaction in settlements
                    ] + [transaction.debited_from for transaction in settlements]

                    self.member_payments: dict[Member, dict[Member, int]] = {
                        member: {} for member in self.members
                    }

                    for transaction in settlements:
                        # print(f"    {transaction.debited_from.name} owes {transaction.currency}{transaction.amount} to {transaction.credited_to.name}")
                        self.member_payments[transaction.credited_to][
                            transaction.debited_from
                        ] = transaction.amount
                        self.member_payments[transaction.debited_from][
                            transaction.credited_to
                        ] = -transaction.amount
                    self.preferred_currency: str = determine_currency_prefix(
                        self.members
                    )

            def __str__(self) -> str:
                string_repr: str = ""

                for member in self.member_payments:
                    if sum(self.member_payments[member].values()) > 0:
                        string_repr += f"\n{member.name} gets {Fore.GREEN}{self.preferred_currency}{sum(self.member_payments[member].values())}{Fore.RESET}\n"
                    else:
                        string_repr += f"\n{member.name} owes {Fore.RED}{self.preferred_currency}{sum(self.member_payments[member].values())}{Fore.RESET}\n"
                    for _ in self.member_payments[member]:
                        if self.member_payments[member][_] > 0:
                            string_repr += f"  {Fore.GREEN}++ {self.preferred_currency}{self.member_payments[member][_]}{Fore.RESET} from {_.name}\n"
                        else:
                            string_repr += f"  {Fore.RED}-- {self.preferred_currency}{-self.member_payments[member][_]}{Fore.RESET} to {_.name}\n"
                return string_repr

        print(f'The settlements to clear all debts in the group "{self.name}" are:')
        print(MemberPayments(settlements))
