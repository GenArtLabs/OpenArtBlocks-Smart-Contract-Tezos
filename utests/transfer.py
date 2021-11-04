def run_tests_transfer(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000
    c1 = FA2(config = config,
        metadata = sp.utils.metadata_of_url("https://example.com"),
        admin = admin.address)

    scenario.h1("Tests transfer")
    scenario.table_of_contents()

    scenario += c1

    scenario.h2("Initial Minting")
    scenario.p("Alice mints a token")
    c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))

    scenario.p("Bob mints a token")
    c1.mint(1).run(sender = bob, amount = sp.mutez(1000000))

    scenario.p("Admin mints a token")
    c1.mint(1).run(sender = admin, amount = sp.mutez(1000000))

    possessors = [alice, bob, admin]
    ownership_test(scenario, c1, possessors)

    scenario.h2("Simple transfer")

    scenario.h3("Valid testcases")

    scenario.h4("Alice sends its token to Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 0)
                                ])
        ]).run(sender = alice)
    possessors[0] = bob
    ownership_test(scenario, c1, possessors)

    scenario.h4("Bob sends its initial token to Alice")
    c1.transfer([
            c1.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 1)
                                ])
        ]).run(sender = bob)
    possessors[1] = alice
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice sends a token to itself")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 1)
                                ])
        ]).run(sender = alice)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice sends its token in 0 amount to someone")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 0,
                                            token_id = 0)
                                ])
        ]).run(sender = alice)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice sends a Bob's token in 0 amount to someone")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 0,
                                            token_id = 0)
                                ])
        ]).run(sender = alice)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Invalid testcases")

    scenario.h4("Alice tries to send a non-existing token in 0 amount to someone")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 0,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to send twice its token (amount) to someone")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 2,
                                            token_id = 0)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to send twice its token (amount) to itself")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 2,
                                            token_id = 0)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to send its initial token to Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 0)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to steal a token from Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 0)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to transfer a non-existing token")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to self-transfer a non-existing token")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h4("Alice tries to steal a non-existing token from Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h2("Test existencee of admin special rights")

    scenario.h3("Admin tries to steal a token from Alice")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 1)
                                ])
        ]).run(sender = admin, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Admin tries to force Alice to give a token to Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1)
                                ])
        ]).run(sender = admin, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Alice tries to transfer a non-existing token")
    c1.transfer([
            c1.batch_transfer.item(from_ = admin.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Admin tries to self-transfer a non-existing token")
    c1.transfer([
            c1.batch_transfer.item(from_ = admin.address,
                                txs = [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Admin tries to steal a non-existing token from Bob")
    c1.transfer([
            c1.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h2("Multiple transfer")

    # Reset contract
    config.max_editions = 10000
    c2 = FA2(config = config,
        metadata = sp.utils.metadata_of_url("https://example.com"),
        admin = admin.address)

    scenario += c2

    scenario.p("Alice mints 3 tokens")
    c2.mint(3).run(sender = alice, amount = sp.mutez(3000000))

    scenario.p("Bob mints 2 tokens")
    c2.mint(2).run(sender = bob, amount = sp.mutez(2000000))

    scenario.p("Admin mints 1 token")
    c2.mint(1).run(sender = admin, amount = sp.mutez(1000000))
    possessors = [alice]*3 + [bob]*2 + [admin]
    ownership_test(scenario, c2, possessors)

    scenario.h3("Valid cases")

    scenario.h4("Alice sends 2 tokens to Bob")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 0)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1)
                                ])
        ]).run(sender = alice)
    possessors[0] = bob
    possessors[1] = bob
    ownership_test(scenario, c2, possessors)

    scenario.h4("Alice sends 2 times the same token to itself")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = alice)
    ownership_test(scenario, c2, possessors)

    scenario.h4("Bob sends 1 token to Alice and 1 token to Admin")
    c2.transfer([
            c2.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 3)
                                ] + [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 4)
                                ])
        ]).run(sender = bob)
    possessors[3] = alice
    possessors[4] = admin
    ownership_test(scenario, c2, possessors)

    scenario.h4("Bob sends 1 token to Admin and twice the same token to itself")
    c2.transfer([
            c2.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 1)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 0)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 0)
                                ])
        ]).run(sender = bob)
    possessors[1] = admin
    ownership_test(scenario, c2, possessors)

    scenario.h4("Alice sends the same token to both itself and Bob")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = alice)
    possessors[2] = bob
    ownership_test(scenario, c2, possessors)

    scenario.h4("Bob sends the same token to both Alice and itself (order)")
    c2.transfer([
            c2.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = alice.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = bob)
    possessors[2] = alice
    ownership_test(scenario, c2, possessors)

    scenario.h3("Invalid cases")

    scenario.h4("Alice sends 1 legit token and 1 non-existing token to Bob")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1000)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c2, possessors)
    scenario.p("Transaction has been cancelled")

    scenario.h4("Alice sends 2 non-existing tokens to Bob")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1000)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 1001)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c2, possessors)

    scenario.h4("Alice sends 2 times the same token to Bob")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c2, possessors)
    scenario.p("Transaction has been cancelled")

    scenario.h4("Alice sends the same token to both Bob and Admin")
    c2.transfer([
            c2.batch_transfer.item(from_ = alice.address,
                                txs = [
                                    sp.record(to_ = bob.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c2, possessors)
    scenario.p("Transaction has been cancelled")

    scenario.h4("Alice tries to force Bob to send 2 tokens to Admin")
    c2.transfer([
            c2.batch_transfer.item(from_ = bob.address,
                                txs = [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 2)
                                ] + [
                                    sp.record(to_ = admin.address,
                                            amount = 1,
                                            token_id = 2)
                                ])
        ]).run(sender = alice, valid=False)
    ownership_test(scenario, c2, possessors)
    scenario.p("Transaction has been cancelled")
