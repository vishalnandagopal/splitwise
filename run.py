# A file containing a sample way to run the program

import random

from classes import Member as Member
from classes import SplitwiseGroup as SplitwiseGroup

v: Member = Member("Vishal")

j: Member = Member("Jahnavi")

x: Member = Member("X")
k: Member = Member("K")

members: tuple[Member, ...] = (v, j, x)

for member in members[1:]:
    v.non_group_transaction(member, random.randint(-1000, 1000))

# print(v.non_group_debts, end="\n\n")
# print(j.non_group_debts)

# print(v.uniq_id_member)

group = SplitwiseGroup("Hyd homies", members)

group.transaction(v, j, random.randint(1, 1000))
group.transaction(x, v, random.randint(1, 1000))
group.transaction(v, x, random.randint(1, 1000))
group.transaction(x, j, random.randint(1, 1000))


if group.first_non_group_transaction:
    group.first_non_group_transaction.recursive_print()
    print()
    group.print_settlements()
