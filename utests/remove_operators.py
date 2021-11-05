def run_tests_remove_operator(config):
    scenario.h1("Removing operator tests")

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
