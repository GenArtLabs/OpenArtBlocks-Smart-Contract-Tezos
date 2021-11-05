def run_tests_lock(config):
    scenario = sp.test_scenario()
    scenario.h1("Lock test")
    scenario.table_of_contents()

    admin, [alice, bob] = get_addresses()

    #-----------------------------------------------------
    scenario.h2("set_base_uri without lock")

    contract = create_new_contract(config, admin, scenario, [alice])

    set_and_test_base_uri('https://example1.com/api/', scenario, contract, admin)
    set_and_test_script('alert(1);', scenario, contract, admin)

    #-----------------------------------------------------
    scenario.h2("Lock")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.lock().run(sender=admin)

    #-----------------------------------------------------
    scenario.h2("Lock from non admin")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.lock().run(sender=alice, valid=False)

    scenario.h3("set_base_uri still possible")
    set_and_test_base_uri('https://example2.com/api/', scenario, contract, admin)
    set_and_test_script('alert(2);', scenario, contract, admin)

    #-----------------------------------------------------
    scenario.h2("set_base_uri impossible after lock")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.lock().run(sender=admin)

    set_and_test_base_uri('https://example3.com/api/',
                          scenario, contract, admin, False)
    set_and_test_script('alert(3);', scenario, contract, admin, False)

    #-----------------------------------------------------
    scenario.h2("Lock activation when lock is already active")

    contract = create_new_contract(config, admin, scenario, [alice])
    contract.lock().run(sender=admin)

    scenario.h3("Over-activation")
    contract.lock().run(sender=admin)

    scenario.h3("set_base_uri impossible with lock")
    set_and_test_base_uri('https://example4.com/api/',
                          scenario, contract, admin, False)
    set_and_test_script('alert(4);', scenario, contract, admin, False)

    #-----------------------------------------------------
    scenario.h2("Lock when all tokens are minted")
    config.max_editions = 1
    contract = create_new_contract(config, admin, scenario, [alice])

    scenario.h3("Mint impossible")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("set_base_uri possible")

    set_and_test_base_uri('https://example1.com/api/', scenario, contract, admin)
    set_and_test_script('alert(1);', scenario, contract, admin)

    scenario.h3("Lock from non-admin")
    contract.lock().run(sender=alice, valid=False)

    scenario.h3("set_base_uri still possible")
    set_and_test_base_uri('https://example2.com/api/', scenario, contract, admin)
    set_and_test_script('alert(2);', scenario, contract, admin)

    scenario.h3("Lock from admin")
    contract.lock().run(sender=admin)

    scenario.h3("set_base_uri impossible with lock")
    set_and_test_base_uri('https://example3.com/api/',
                          scenario, contract, admin, False)
    set_and_test_script('alert(3);', scenario, contract, admin, False)
