# (c) Copyright 2021 by Coinkite Inc. This file is covered by license found in COPYING-CC.
#
# Seed XOR Feature
# - use bitwise XOR on 24-word phrases
# - for secret spliting on paper
# - all combination of partial XOR seed phrases are working wallets
#
import stash, ngu, chains, bip39, random
from ux import ux_show_story, ux_enter_number, the_ux, ux_confirm, ux_dramatic_pause
from seed import word_quiz, WordNestMenu, set_seed_value
from nvstore import settings

def xor32(*args):
    # bit-wise xor between all args
    rv = bytearray(32)

    for i in range(32):
        for a in args:
            rv[i] ^= a[i]

    return rv

async def xor_split_start(*a):

    ch = await ux_show_story('''\
XOR Seed Split

This feature splits your BIP-39 seed phrase into multiple parts. \
Each part is 24 words and looks and functions as a normal BIP-39 wallet.

We recommend spliting into just two parts, but permit up to four.

If ANY ONE of the parts is lost, then ALL FUNDS are lost and the original \
seed phrase cannot be reconstructed.

Finding a single part does not help an attacker construct the original seed.

Funds could probably be recovered if single-word transcription errors are made, but \
ALL FUNDS will certainly be lost if 24 words are lost.

Press from 2, 3 or 4 to select number of parts. ''', strict_escape=True, escape='234x')
    if ch == 'x': return

    num_parts = int(ch)

    ch = await ux_show_story('''\
Split Into {n} Parts

On the following screen you will be shown {n} lists of 24-words. \
The new words, when reconstructed, will re-create the seed already \
in use on this Coldcard.

The new parts are generated deterministically from your seed, so if you \
repeat this process later, the same {t} words will be shown.

If you would prefer a random split using the TRNG, press (2). \
Otherwise, press OK to continue.'''.format(n=num_parts, t=num_parts*24), escape='2')

    use_rng = (ch == '2')
    if ch == 'x': return

    await ux_dramatic_pause('Generating...', 2)

    raw_secret = bytes(32)
    try:
        with stash.SensitiveValues() as sv:
            words = None
            if sv.mode == 'words':
                words = bip39.b2a_words(sv.raw).split(' ')

            if not words or len(words) != 24:
                await ux_show_story("Need 24-seed words for this feature.")
                return

            # checksum of target result is useful.
            chk_word = words[-1]

            # going to need the secret
            raw_secret = sv.raw
            assert len(raw_secret) == 32
    
        parts = []
        for i in range(num_parts-1):
            if use_rng:
                here = random.bytes(32)
                assert len(set(here)) > 4       # TRNG failure?
                mask = ngu.hash.sha256d(here)
            else:
                mask = ngu.hash.sha256d(b'Batshitoshi ' + raw_secret 
                                            + b'%d of %d parts' % (i, num_parts))
            parts.append(mask)

        parts.append(xor32(raw_secret, *parts))

        assert xor32(*parts) == raw_secret      # selftest

    finally:
        stash.blank_object(raw_secret)

    words = [bip39.b2a_words(p).split(' ') for p in parts]

    while 1:
        ch = await show_n_parts(num_parts, words, chk_word)
        if ch == 'x': 
            if not use_rng: return
            if await ux_confirm("Stop and forget those words?"):
                return
            continue

        for ws, part in enumerate(words):
            ch = await word_quiz(part, title='Word %s%%d is?' % chr(65+ws))
            if ch == 'x': break
        else:
            break

# list of seed phrases
import_xor_parts = []

class XORWordNestMenu(WordNestMenu):
    @staticmethod
    async def all_done(new_words):
        # So we have another part, might be done or not.
        global import_xor_parts
        assert len(new_words) == 24
        import_xor_parts.append(new_words)

        XORWordNestMenu.pop_all()

        num_parts = len(import_xor_parts)
        seed = xor32(*(bip39.a2b_words(w) for w in import_xor_parts))

        msg = "You've entered %d parts so far.\n\n" % num_parts
        if num_parts >= 2:
            chk_word = bip39.b2a_words(seed).split(' ')[-1]
            msg += "If you stop now, the 24th word of the XOR-combined seed phrase\nwill be:\n\n"
            msg += "24: %s\n\n" % chk_word
        msg += "Press (1) to enter next list of words, or (2) if done with all words."

        ch = await ux_show_story(msg, strict_escape=True, escape='12x', sensitive=True)

        if ch == 'x':
            # give up
            import_xor_parts.clear()          # concern: contaminated w/ secrets
            goto_top_menu()
        elif ch == '1':
            # do another list of words
            nxt = XORWordNestMenu(num_words=24)
            the_ux.push(nxt)
        elif ch == '2':
            # done; import on temp basis, or be the main secret
            from pincodes import pa
            enc = stash.SecretStash.encode(seed_phrase=seed)

            if pa.is_secret_blank():
                # save it since they have no other secret
                set_seed_value(encoded=enc)
            else:
                pa.tmp_secret(enc)
                await ux_show_story("New master key in effect until next power down.")

        return None

    def tr_label(self):
        global import_xor_parts
        pn = len(import_xor_parts)
        return chr(65+pn) + ' Word' 

async def show_n_parts(num_parts, words, chk_word):
    msg = 'Record these %d lists of 24-words each.\n\n' % num_parts

    for n,words in enumerate(words):
        msg += 'Part %s:\n' % chr(65+n)
        msg += '\n'.join('%2d: %s' % (i+1, w) for i,w in enumerate(words))
        msg += '\n\n'

    msg += 'The correctly reconstructed seed phrase will have this final word, which we recommend recording:\n\n24: %s' % chk_word

    msg += '\n\nPlease check and double check your notes. There will be a test! ' 

    return await ux_show_story(msg, sensitive=True)

async def xor_restore_start(*a):
    # shown on import menu when no seed of any kind yet
    # - or operational system
    await ux_show_story('''\
To import a seed split using XOR, you must import all the parts.
It does not matter the order (A/B/C or C/A/B) and the Coldcard
cannot determine when you have all the parts. You may stop at
any time and you will have a valid wallet.''')
    global import_xor_parts
    import_xor_parts.clear()

    from pincodes import pa

    if not pa.is_secret_blank():
        msg = "Since you have a seed already on this Coldcard, the reconstructed XOR seed will be temporary and not saved. Please wipe the seed if you want to commit the new value into the secure element."
        if settings.get('words', False):
            msg += '''\n
Press (1) to include this Coldcard's seed words into the XOR seed set.'''

        ch = await ux_show_story(msg, escape='1')

        if ch == '1':
            with stash.SensitiveValues() as sv:
                if sv.mode == 'words':
                    words = bip39.b2a_words(sv.raw).split(' ')
                    import_xor_parts.append(words)

    return XORWordNestMenu(num_words=24)

# EOF