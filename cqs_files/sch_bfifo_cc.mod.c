#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/export-internal.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

#ifdef CONFIG_UNWINDER_ORC
#include <asm/orc_header.h>
ORC_HEADER;
#endif

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_MITIGATION_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

KSYMTAB_DATA(bfifo_cc_qdisc_ops, "", "");

SYMBOL_CRC(bfifo_cc_qdisc_ops, 0x1badaea8, "");

static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0xa755349f, "unregister_qdisc" },
	{ 0xc3690fc, "_raw_spin_lock_bh" },
	{ 0x4b440f57, "kmem_cache_free" },
	{ 0xe46021ca, "_raw_spin_unlock_bh" },
	{ 0x85670f1d, "rtnl_is_locked" },
	{ 0x7baaefe8, "rtnl_kfree_skbs" },
	{ 0x56470118, "__warn_printk" },
	{ 0x54b1fac6, "__ubsan_handle_load_invalid_value" },
	{ 0xa20d01ba, "__trace_bprintk" },
	{ 0x1283e5b5, "qdisc_tree_reduce_backlog" },
	{ 0x11716a44, "kmem_cache_alloc" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x445c10bd, "nla_put" },
	{ 0xf0fdf6cb, "__stack_chk_fail" },
	{ 0x143360cb, "kmem_cache_create" },
	{ 0x790f5c3d, "register_qdisc" },
	{ 0xb1e25684, "__trace_bputs" },
	{ 0x1d465efd, "kmem_cache_destroy" },
	{ 0x907364e, "module_layout" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "683A83FEDC497477EA7C808");
