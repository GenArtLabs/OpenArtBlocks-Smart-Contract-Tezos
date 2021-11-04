def run_tests_operator(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000
    c1 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)

    scenario.h1("Tests operator")

    scenario.table_of_contents()

    scenario.h2("Operator basic tests")

    scenario += c1

    scenario.p("Creates one operator")
    op = sp.test_account("Operator")

    scenario.p("Alice mints 3 tokens")
    c1.mint(3).run(sender=alice, amount=sp.mutez(3000000))
    possessors = [alice]*3

    scenario.h3(
        "Operator tries to transfer Alice's token before being permitted to")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Alice grants Operator rights on token 0 and 2")

    c1.update_operators([
        sp.variant("add_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
        sp.variant("add_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=2))
    ]).run(sender=alice)

    scenario.h3("Operator transfers token 0 from Alice to Bob")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, c1, possessors)

    scenario.h3("Operator tries to transfer token 0 from Bob to Alice")

    c1.transfer([
        c1.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Alice transfers token 2 to Bob")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=2)
                               ])
    ]).run(sender=alice)
    possessors[2] = bob
    ownership_test(scenario, c1, possessors)

    scenario.h3("Operator is too late and tries to transfer token 2 to Admin")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Bob sends back its tokens to Alice")

    c1.transfer([
        c1.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ] + [
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=2)
                               ])
    ]).run(sender=bob)
    possessors[0] = alice
    possessors[2] = alice
    ownership_test(scenario, c1, possessors)

    scenario.h3("Operator transfers again token 0 from Alice to Bob")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, c1, possessors)

    scenario.h3("Bob gives Operator right to transfer its token 0")

    c1.update_operators([
        sp.variant("add_operator", c1.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.h3("Operator transfers token 0 from Bob to Alice")

    c1.transfer([
        c1.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = alice
    ownership_test(scenario, c1, possessors)

    scenario.h2("Token loopback: does not cancels operator rights")

    scenario.h3("Alice grants Operator rights on token 0")

    c1.update_operators([
        sp.variant("add_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Alice transfers token 0 to itself")

    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, c1, possessors)

    scenario.h3("Operator still have rights to token 0")
    c1.transfer([
        c1.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, c1, possessors)

    scenario.h2("Naming operator on balance 0 token")

    config.max_editions = 10000
    c2 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c2

    scenario.p("Alice mints 1 token")
    c2.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    possessors = [alice]
    ownership_test(scenario, c2, possessors)

    scenario.h3("Bob names operator for token 0 he doesn't possess yet")

    c2.update_operators([
        sp.variant("add_operator", c2.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.h3(
        "Alice sends token 0 to Bob. Operator then has right on this token.")

    c2.transfer([
        c2.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    possessors[0] = bob
    ownership_test(scenario, c2, possessors)

    c2.transfer([
        c2.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = alice
    ownership_test(scenario, c2, possessors)

    scenario.h2("Granting in the name of someone else")

    scenario.h3("Admin tries to grant Operator rights on Alice's token 0")

    c2.update_operators([
        sp.variant("add_operator", c2.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=admin, valid=False)

    scenario.h3("Bob tries to grant Operator rights on Alice's token 0")

    c2.update_operators([
        sp.variant("add_operator", c2.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob, valid=False)

    scenario.h3("Alice itself cannot fake token owner in update_operators")

    c2.update_operators([
        sp.variant("add_operator", c2.operator_param.make(
            owner=admin.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice, valid=False)

    scenario.h2("Multiple operators tests")

    op2 = sp.test_account("Operator#2")

    config.max_editions = 10000
    c3 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c3

    scenario.p("Alice mints 3 token")
    c3.mint(3).run(sender=alice, amount=sp.mutez(3000000))

    scenario.p("Operator#1 mints a token")
    c3.mint(1).run(sender=op, amount=sp.mutez(1000000))

    possessors = [alice]*3 + [op]
    ownership_test(scenario, c3, possessors)

    scenario.p("Alice names Operator#1 as operator for token 0")

    c3.update_operators([
        sp.variant("add_operator", c3.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Operator#1 names Operator#2 as operator for non possessed token 0")

    c3.update_operators([
        sp.variant("add_operator", c3.operator_param.make(
            owner=op.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=op)

    scenario.h3(
        "No operator transitivity: Operator#2 tries to smuggle token 0 of Alice via Operator#1")

    c3.transfer([
        c3.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op2, valid=False)
    ownership_test(scenario, c3, possessors)

    scenario.h3(
        "Operator#1 cannot name Operator#2 as operator on Alice's token 0")

    c3.update_operators([
        sp.variant("add_operator", c3.operator_param.make(
            owner=alice.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=op, valid=False)

    scenario.h3("Alice can name two operators on the same token")

    c3.update_operators([
        sp.variant("add_operator", c3.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1)), sp.variant("add_operator", c3.operator_param.make(
                owner=alice.address,
                operator=op2.address,
                token_id=1))
    ]).run(sender=alice)

    c3.transfer([
        c3.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=op)
    possessors[1] = bob
    ownership_test(scenario, c3, possessors)

    scenario.h3("Alice grants access to 2 tokens to the same operator")

    c3.update_operators([
        sp.variant("add_operator", c3.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)), sp.variant("add_operator", c3.operator_param.make(
                owner=alice.address,
                operator=op.address,
                token_id=2))
    ]).run(sender=alice)

    c3.transfer([
        c3.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ] + [
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=2)
                               ])
    ]).run(sender=op)
    possessors[2] = bob
    ownership_test(scenario, c3, possessors)

    scenario.h2("Removing operator tests")

    config.max_editions = 10000
    c4 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c4

    scenario.p("Alice mints 3 tokens")
    c4.mint(3).run(sender=alice, amount=sp.mutez(3000000))
    possessors = [alice]*3
    ownership_test(scenario, c4, possessors)

    scenario.h3("Removing non-added operator")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Removing non-added operator on non-possessed token")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=bob)

    scenario.h3("Bob tries to remove non-added operator on non-existing token")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=1000)),
    ]).run(sender=bob, valid=False)

    scenario.h3("Removed operator tries to transfer Alice's token 0")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c4, possessors)

    scenario.h3("Alice adds then removes operator")

    c4.update_operators([
        sp.variant("add_operator", c4.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Removed operator tries to transfer Alice's token 0")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c4, possessors)

    # TODO: operator loopback alice -> alice

    scenario.h3("Alice adds operator on multiple tokens")

    c4.update_operators([
        sp.variant("add_operator", c4.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ] + [
        sp.variant("add_operator", c4.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1))

    ]).run(sender=alice)

    scenario.h3("Alice removes operator on token 0")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Operator tries to smuggle both tokens at once")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ] + [
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c4, possessors)

    scenario.h3("Operator sends its granted token 1 to Bob")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=op)
    possessors[1] = bob
    ownership_test(scenario, c4, possessors)

    scenario.h3("Alice removes operator on token 1 and gets back it token")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1)),
    ]).run(sender=alice)

    c4.transfer([
        c4.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=op)
    possessors[1] = alice
    ownership_test(scenario, c4, possessors)

    scenario.h3("Removed operator tries to transfer Alice's token 1")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c4, possessors)

    scenario.h3("Alice adds two different operators on the same token 0")

    c4.update_operators([
        sp.variant("add_operator", c4.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("add_operator", c4.operator_param.make(
            owner=alice.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Alice removes Operator#1 on this token 0")

    c4.update_operators([
        sp.variant("remove_operator", c1.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Operator#2 still can smuggle token 0")

    c4.transfer([
        c4.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op2)
    possessors[0] = bob
    ownership_test(scenario, c4, possessors)

    scenario.h3(
        "Bob adds THEN removes Operator#1 during the same request on token 0")

    c4.update_operators([
        sp.variant("add_operator", c4.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("remove_operator", c4.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.h3("Operator#1 should not smuggle Bob's token 0")

    c4.transfer([
        c4.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, c4, possessors)

    scenario.h3(
        "Bob removes THEN adds Operator#1 during the same request on token 0")

    c4.update_operators([
        sp.variant("remove_operator", c4.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("add_operator", c4.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.h3("Operator#1 should be able to smuggle Bob's token 0")

    c4.transfer([
        c4.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = alice
    ownership_test(scenario, c4, possessors)
