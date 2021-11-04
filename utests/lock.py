def run_tests_lock(config):
    scenario = sp.test_scenario()
    scenario.h1("Lock test")
    scenario.table_of_contents()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000

    c1 = FA2(config = config,
        metadata = sp.utils.metadata_of_url("https://example.com"),
        admin = admin.address)
    scenario += c1

    scenario.h2("Initial minting")
    minted = c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))

    scenario.h3("set_base_uri without lock")
    set_and_test_base_uri('https://example1.com/api/', scenario, c1, admin)
    set_and_test_script('alert(1);', scenario, c1, admin)

    scenario.h2("Lock")

    scenario.h3("Lock from non-admin")
    c1.lock().run(sender = alice, valid = False)

    scenario.h3("set_base_uri still possible")
    set_and_test_base_uri('https://example2.com/api/', scenario, c1, admin)
    set_and_test_script('alert(2);', scenario, c1, admin)

    scenario.h3("Lock from admin")
    c1.lock().run(sender = admin)

    scenario.h3("set_base_uri impossible with lock")
    set_and_test_base_uri('https://example3.com/api/', scenario, c1, admin, False)
    set_and_test_script('alert(3);', scenario, c1, admin, False)

    scenario.h2("Lock activation when lock is already active")

    scenario.h3("Over-activation")
    c1.lock().run(sender = admin)

    scenario.h3("set_base_uri still impossible with lock")
    set_and_test_base_uri('https://example4.com/api/', scenario, c1, admin, False)
    set_and_test_script('alert(4);', scenario, c1, admin, False)

    scenario.h2("Lock when all tokens are minted (new contract)")
    config.max_editions = 1
    c2 = FA2(config = config,
        metadata = sp.utils.metadata_of_url("https://example.com"),
        admin = admin.address)
    scenario += c2

    scenario.h3("set_base_uri possible when all tokens have been minted")
    c2.mint(1).run(sender = alice, amount = sp.mutez(1000000))
    c2.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)
    set_and_test_base_uri('https://example1.com/api/', scenario, c2, admin)
    set_and_test_script('alert(1);', scenario, c2, admin)

    scenario.h3("Lock from non-admin")
    c2.lock().run(sender = alice, valid = False)

    scenario.h3("set_base_uri still possible")
    set_and_test_base_uri('https://example2.com/api/', scenario, c2, admin)
    set_and_test_script('alert(2);', scenario, c2, admin)

    scenario.h3("Lock from admin")
    c2.lock().run(sender = admin, valid = True)

    scenario.h3("set_base_uri impossible with lock")
    set_and_test_base_uri('https://example3.com/api/', scenario, c2, admin, False)
    set_and_test_script('alert(3);', scenario, c2, admin, False)
