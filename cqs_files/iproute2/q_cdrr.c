/* SPDX-License-Identifier: GPL-2.0-or-later */
/*
 * q_cdrr.c		Colored-Based DRR.
 *
 * Authors:	Aitor Encinas Alonso, <aitor.encinas.alonso@alumnos.upm.es>
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>

#include "utils.h"
#include "tc_util.h"

#define DRR_DEFAULT_TMAX 1500
#define DRR_DEFAULT_MODE 0

enum {
	TCA_MYDRR_UNSPEC,
	TCA_MYDRR_QUANTUM,
	TCA_MYDRR_TMAX,
	TCA_MYDRR_MODE,
	__TCA_MYDRR_MAX
};

#define TCA_MYDRR_MAX	(__TCA_MYDRR_MAX - 1)

static void explain(void)
{
	fprintf(stderr, "Usage: ... drr\n");
}

static void explain2(void)
{
    fprintf(stderr,
        "Usage: ... drr quantum SIZE tmax BYTES mode MODE\n");
}

static int drr_parse_opt(const struct qdisc_util *qu, int argc, char **argv,
			 struct nlmsghdr *n, const char *dev)
{
	while (argc) {
		if (strcmp(*argv, "help") == 0) {
			explain();
			return -1;
		} else {
			fprintf(stderr, "What is \"%s\"?\n", *argv);
			explain();
			return -1;
		}
	}
	return 0;
}

static int drr_parse_class_opt(const struct qdisc_util *qu, int argc, char **argv,
			       struct nlmsghdr *n, const char *dev)
{
	struct rtattr *tail;
	__u32 tmp;
	__u32 tmax = DRR_DEFAULT_TMAX;
	__u32 mode = DRR_DEFAULT_MODE;

	tail = addattr_nest(n, 1024, TCA_OPTIONS);

	while (argc > 0) {
		if (strcmp(*argv, "quantum") == 0) {
			NEXT_ARG();
			if (get_size(&tmp, *argv)) {
				fprintf(stderr, "Illegal \"quantum\"\n");
				return -1;
			}
		} else if (strcmp(*argv, "tmax") == 0) {
            NEXT_ARG();
            if (get_u32(&tmax, *argv, 0)) {
                fprintf(stderr, "Invalid tmax\n");
                return -1;
            }
		} else if (strcmp(*argv, "mode") == 0) {
            NEXT_ARG();
            if (get_u32(&mode, *argv, 0)) {
                fprintf(stderr, "Invalid mode\n");
                return -1;
            }
			if (mode != 0 && mode != 1) {
        		fprintf(stderr, "Mode must be 0 or 1\n");
        		return -1;
    		}
		} else if (strcmp(*argv, "help") == 0) {
			explain2();
			return -1;
		} else {
			fprintf(stderr, "What is \"%s\"?\n", *argv);
			explain2();
			return -1;
		}
		argc--; argv++;
	}

	addattr_l(n, 1024, TCA_MYDRR_QUANTUM, &tmp, sizeof(tmp));
    addattr_l(n, 1024, TCA_MYDRR_TMAX, &tmax, sizeof(tmax));
	addattr_l(n, 1024, TCA_MYDRR_MODE, &mode, sizeof(mode));
	addattr_nest_end(n, tail);
	return 0;
}

static int drr_print_opt(const struct qdisc_util *qu, FILE *f, struct rtattr *opt)
{
	struct rtattr *tb[TCA_MYDRR_MAX + 1];

	if (opt == NULL)
		return 0;

	parse_rtattr_nested(tb, TCA_MYDRR_MAX, opt);

	if (tb[TCA_MYDRR_QUANTUM])
		print_size(PRINT_FP, NULL, "quantum %s ",
			   rta_getattr_u32(tb[TCA_MYDRR_QUANTUM]));
	if (tb[TCA_MYDRR_TMAX])
		print_uint(PRINT_FP, NULL, "tmax %u ",
			   rta_getattr_u32(tb[TCA_MYDRR_TMAX]));
	if (tb[TCA_MYDRR_MODE])
		print_uint(PRINT_FP, NULL, "mode %u ",
			   rta_getattr_u32(tb[TCA_MYDRR_MODE]));
	return 0;
}

static int drr_print_xstats(const struct qdisc_util *qu, FILE *f, struct rtattr *xstats)
{
	struct tc_drr_stats *x;

	if (xstats == NULL)
		return 0;
	if (RTA_PAYLOAD(xstats) < sizeof(*x))
		return -1;
	x = RTA_DATA(xstats);

	print_size(PRINT_FP, NULL, " deficit %s ", x->deficit);
	return 0;
}

struct qdisc_util cdrr_qdisc_util = {
	.id		= "cdrr",
	.parse_qopt	= drr_parse_opt,
	.print_qopt	= drr_print_opt,
	.print_xstats	= drr_print_xstats,
	.parse_copt	= drr_parse_class_opt,
	.print_copt	= drr_print_opt,
};
