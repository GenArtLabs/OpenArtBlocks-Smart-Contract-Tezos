def run_tests_does_token_exist(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests does token exist")

    #-----------------------------------------------------
    scenario.h2("Non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    scenario.verify(contract.does_token_exist(0) == False)

    #-----------------------------------------------------
    # scenario.h2("Invalid token")

    # contract = create_new_contract(config, admin, scenario, [])

    # scenario.verify(contract.does_token_exist(-1) == False)

    #-----------------------------------------------------
    scenario.h2("Existing token")

    contract = create_new_contract(config, admin, scenario, [alice])

    scenario.verify(contract.does_token_exist(0) == True)
