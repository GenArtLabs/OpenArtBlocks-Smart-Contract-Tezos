def run_tests_all_tokens(config):
    return
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests all_tokens")

    #-----------------------------------------------------
    scenario.h2("No token")

    contract = create_new_contract(config, admin, scenario, [])

    all_tokens = contract.all_tokens()
    scenario.verify(all_tokens == sp.range(0, 0))

    #-----------------------------------------------------
    scenario.h2("One token")

    contract = create_new_contract(config, admin, scenario, [alice])

    all_tokens = contract.all_tokens()
    scenario.verify(all_tokens == sp.range(0, 1))

    #-----------------------------------------------------
    scenario.h2("Two tokens")

    contract = create_new_contract(config, admin, scenario, [alice, bob])

    all_tokens = contract.all_tokens()
    scenario.verify(all_tokens == sp.range(0, 2))
