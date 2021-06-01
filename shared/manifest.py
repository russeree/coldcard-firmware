# Freeze everything in this list.
# - not optimized because we need asserts to work
# - for mk3 vs mk4, see manifest_mk[34].py
freeze_as_mpy('', [
	'actions.py',
	'address_explorer.py',
	'auth.py',
	'backups.py',
	'callgate.py',
	'chains.py',
	'choosers.py',
	'compat7z.py',
	'descriptor.py',
	'dev_helper.py',
	'display.py',
	'drv_entro.py',
	'exceptions.py',
	'export.py',
	'files.py',
	'flow.py',
	'glob.py',
	'h.py',
	'history.py',
	'hsm.py',
	'hsm_ux.py',
	'imptask.py',
	'login.py',
	'main.py',
	'mempad.py',
	'menu.py',
	'multisig.py',
	'numpad.py',
	'nvstore.py',
	'opcodes.py',
	'paper.py',
	'pincodes.py',
	'psbt.py',
	'pwsave.py',
	'queues.py',
	'random.py',
	'seed.py',
	'selftest.py',
	'serializations.py',
	'sffile.py',
	'sflash.py',
	'sram2.py',
	'ssd1306.py',
	'stash.py',
	'usb.py',
	'users.py',
	'utils.py',
	'ux.py',
	'version.py',
	'xor_seed.py',
], opt=0)

# Optimize data-like files, since no need to debug them.
freeze_as_mpy('', [
	'sigheader.py',
	'graphics.py',
	'zevvpeep.py',
	'public_constants.py',
], opt=3)
