def run_tests_set_administrator(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests set administrator")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Admin sets Bob as administrator")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_administrator(bob.address).run(sender=admin)

    scenario.h3("Bob can now pause mint")

    contract.set_pause(True).run(sender=bob)

    #-----------------------------------------------------
    scenario.h2("Admin cannot use admin rights after granting Bob")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_administrator(bob.address).run(sender=admin)

    contract.set_pause(True).run(sender=admin, valid=False)

    #-----------------------------------------------------
    scenario.h2("Admin sets Bob as administrator")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_administrator(bob.address).run(sender=bob, valid=False)

    scenario.h3("Bob has no administrator rights")

    contract.set_pause(True).run(sender=bob, valid=False)
