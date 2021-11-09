def run_mint_test(config):
    scenario = sp.test_scenario()
    scenario.h1("Mint test")
    scenario.table_of_contents()

    admin, [alice, bob] = get_addresses()

    c1 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c1

    scenario.h2("Single minting")
    scenario.h3("Mint 1 token from non-admin (OK)")
    c1.mint(1).run(sender=alice, amount=sp.mutez(config.price))
    scenario.verify(c1.data.ledger[0] == alice.address)
    scenario.h3("Mint 1 token from admin (OK)")
    c1.mint(1).run(sender=admin, amount=sp.mutez(config.price))
    scenario.verify(c1.data.ledger[1] == admin.address)

    scenario.h2("Negative minting")
    scenario.h3("Mint -1 tokens from non-admin (KO)")
    c1.mint(-1).run(sender=alice, amount=sp.mutez(0), valid=False)
    scenario.h3("Mint -1 tokens from admin (KO)")
    c1.mint(-1).run(sender=admin, amount=sp.mutez(0), valid=False)

    scenario.h2("Zero minting")
    scenario.h3("Mint 0 tokens from non-admin (KO)")
    c1.mint(0).run(sender=alice, amount=sp.mutez(0), valid=False)
    scenario.h3("Mint 0 tokens from admin (KO)")
    c1.mint(0).run(sender=admin, amount=sp.mutez(0), valid=False)

    scenario.h2("Multiple minting")
    scenario.h3("Mint 3 tokens from non-admin (OK)")
    c1.mint(3).run(sender=alice, amount=sp.mutez(config.price * 3))
    for i in range(2, 5):
        scenario.verify(c1.data.ledger[i] == alice.address)
    scenario.h3("Mint 11 tokens from non-admin (OK)")
    c1.mint(11).run(sender=alice, amount=sp.mutez(config.price * 11))
    for i in range(5, 16):
        scenario.verify(c1.data.ledger[i] == alice.address)

    if (config.price > 0):
        scenario.h2("Incoherent amount (0)")
        scenario.h3("Mint 1 token from non-admin for amount=0 (KO)")
        c1.mint(1).run(sender=alice, amount=sp.mutez(0), valid=False)
        scenario.h3("Mint 1 token from admin for amount=0 (KO)")
        c1.mint(1).run(sender=admin, amount=sp.mutez(0), valid=False)

        scenario.h2("Incoherent amount (lower)")
        scenario.h3("Mint 1 token from non-admin for amount=price-1 (KO)")
        c1.mint(1).run(sender=alice, amount=sp.mutez(
            config.price - 1), valid=False)
        scenario.h3("Mint 1 token from admin for amount=price-1 (KO)")
        c1.mint(1).run(sender=admin, amount=sp.mutez(
            config.price - 1), valid=False)

    scenario.h2("Incoherent amount (greater)")
    scenario.h3("Mint 1 token from non-admin for amount=price+1 (KO)")
    c1.mint(1).run(sender=alice, amount=sp.mutez(
        config.price + 1), valid=False)
    scenario.h3("Mint 1 token from admin for amount=price+1 (KO)")
    c1.mint(1).run(sender=admin, amount=sp.mutez(
        config.price + 1), valid=False)

    scenario.h2("Pause")
    scenario.h3("Pause activation from admin (OK)")
    c1.set_pause(True).run(sender=admin)
    scenario.h3("Mint 1 token from non-admin (KO)")
    c1.mint(1).run(sender=alice, amount=sp.mutez(config.price), valid=False)
    scenario.h3("Mint 1 token from admin (KO)")
    c1.mint(1).run(sender=admin, amount=sp.mutez(config.price), valid=False)

    scenario.h2("Unpause")
    scenario.h3("Pause deactivation from admin (OK)")
    c1.set_pause(False).run(sender=admin)
    scenario.h3("Mint 1 token from non-admin (OK)")
    c1.mint(1).run(sender=alice, amount=sp.mutez(config.price))
    scenario.verify(c1.data.ledger[16] == alice.address)
    scenario.h3("Mint 1 token from admin (OK)")
    c1.mint(1).run(sender=admin, amount=sp.mutez(config.price))
    scenario.verify(c1.data.ledger[17] == admin.address)

    scenario.h2("Max editions reached (new contract with max_editions=1)")
    config.max_editions = 1
    c2 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c2

    scenario.h3("Mint more tokens than available")
    scenario.h4("Mint 2 tokens from non-admin (KO)")
    c2.mint(2).run(sender=alice, amount=sp.mutez(
        config.price * 2), valid=False)
    scenario.h4("Mint 2 tokens from admin (KO)")
    c2.mint(2).run(sender=admin, amount=sp.mutez(
        config.price * 2), valid=False)

    scenario.h3("Mint until max is reached")
    scenario.h4("Mint 1 token from non-admin (OK)")
    c2.mint(1).run(sender=alice, amount=sp.mutez(config.price))
    scenario.verify(c1.data.ledger[0] == alice.address)

    scenario.h3("Mint 1 token after max is reached")
    scenario.h4("Mint 1 token from non-admin (KO)")
    c2.mint(1).run(sender=alice, amount=sp.mutez(config.price), valid=False)
    scenario.h4("Mint 1 token from admin (KO)")
    c2.mint(1).run(sender=admin, amount=sp.mutez(config.price), valid=False)
