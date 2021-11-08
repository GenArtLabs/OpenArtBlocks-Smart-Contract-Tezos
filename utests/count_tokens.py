def run_tests_count_tokens(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests count token")

    #-----------------------------------------------------
    scenario.h2("Nothing is minted")
    contract = create_new_contract(config, admin, scenario, [])

    count = contract.count_tokens()
    scenario.verify(count == 0)

    #-----------------------------------------------------
    scenario.h2("One token is minted")
    contract = create_new_contract(config, admin, scenario, [alice])

    count = contract.count_tokens()
    scenario.verify(count == 1)

    #-----------------------------------------------------
    scenario.h2("Two token are minted")
    contract = create_new_contract(config, admin, scenario, [alice])

    count = contract.count_tokens()
    scenario.verify(count == 1)

    contract.mint(1).run(sender=admin, amount=sp.mutez(1000000))

    count = contract.count_tokens()
    scenario.verify(count == 2)

    #-----------------------------------------------------
    scenario.h2("Mint fails are not counted as tokens")
    config.max_editions = 2
    contract = create_new_contract(config, admin, scenario, [alice, bob])

    count = contract.count_tokens()
    scenario.verify(count == 2)

    contract.mint(1).run(sender=admin, amount=sp.mutez(1000000), valid=False)

    count = contract.count_tokens()
    scenario.verify(count == 2)
