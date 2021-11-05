def run_token_metadata(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests token metadata")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Get token metadata")
    contract = create_new_contract(config, admin, scenario, [alice])

    scenario.show(contract.token_metadata(0))

    #-----------------------------------------------------
    scenario.h2("Get non-existing token metadata")
    contract = create_new_contract(config, admin, scenario, [])

    # TODO: catch error, this is supposed to fail
    # scenario.show(contract.token_metadata(0))
