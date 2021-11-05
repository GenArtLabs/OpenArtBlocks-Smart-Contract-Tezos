def run_tests_mutez_transfer(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests mutez transfer")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Admin cashes out all contract's mutez")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(1000000),
        destination=admin.address,
    ).run(sender=admin)

    scenario.verify(contract.balance == sp.mutez(0))

    #-----------------------------------------------------
    scenario.h2("Admin cashes out partial contract's mutez")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(1),
        destination=admin.address,
    ).run(sender=admin)

    scenario.verify(contract.balance == sp.mutez(999999))

    #-----------------------------------------------------
    scenario.h2("Admin cashes out more mutez than possible")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(2000000),
        destination=admin.address,
    ).run(sender=admin, valid=False)

    #-----------------------------------------------------
    scenario.h2("Bob tries to cash out")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(1),
        destination=bob.address,
    ).run(sender=bob, valid=False)

    scenario.verify(contract.balance == sp.mutez(1000000))

    #-----------------------------------------------------
    scenario.h2("Bob tries to cash out more than possible")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(2000000),
        destination=bob.address,
    ).run(sender=bob, valid=False)

    scenario.verify(contract.balance == sp.mutez(1000000))

    #-----------------------------------------------------
    scenario.h2("Admin cashes out in several time")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.mutez_transfer(
        amount=sp.mutez(500000),
        destination=bob.address,
    ).run(sender=admin)

    scenario.verify(contract.balance == sp.mutez(500000))

    scenario.h3("Bob tries to cash out")
    contract.mutez_transfer(
        amount=sp.mutez(500000),
        destination=bob.address,
    ).run(sender=bob, valid=False)

    scenario.verify(contract.balance == sp.mutez(500000))

    contract.mutez_transfer(
        amount=sp.mutez(499999),
        destination=bob.address,
    ).run(sender=admin)

    scenario.verify(contract.balance == sp.mutez(1))

    contract.mutez_transfer(
        amount=sp.mutez(100),
        destination=bob.address,
    ).run(sender=admin, valid=False)

    scenario.verify(contract.balance == sp.mutez(1))

    contract.mutez_transfer(
        amount=sp.mutez(1),
        destination=bob.address,
    ).run(sender=admin)

    scenario.verify(contract.balance == sp.mutez(0))

    contract.mutez_transfer(
        amount=sp.mutez(100),
        destination=bob.address,
    ).run(sender=admin, valid=False)

    scenario.verify(contract.balance == sp.mutez(0))
