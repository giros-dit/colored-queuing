/* SPDX-License-Identifier: GPL-2.0-or-later */
/*
 * q_bfifo_cc.c		AQM HCTNS queue userspace parser for bfifo_cc qdisc
 *
 * Matches kernel module sch_bfifo_cc
 *
 * Authors:	Aitor Encinas Alonso <aitor.encinas.alonso@alumnos.upm.es>
 */

 #include <stdio.h>
 #include <stdlib.h>
 #include <unistd.h>
 #include <string.h>
 #include <linux/tc_bfifo_cc.h>
 
 #include "utils.h"
 #include "tc_util.h"

 static void explain(void)
{
	fprintf(stderr, "Usage: ... bfifo_cc [ limit NUMBER_BYTES ] [threshold NUMBER_BYTES] \n");
}

 /*
 * bfifo_cc_parse_opt: Parses the options for the bfifo_cc qdisc
 * qu: pointer to the qdisc_util structure
 * argc,argv used for parsing arguments of type limit 1000, argc is the number of arguments and argv a vector of arguments
 * n is a pointer to the Netlink message which will be sent to the kernel
 * dev is the name of the device
 * opt is the structure that will be filled with the parsed options;
 */
 static int bfifo_cc_parse_opt(const struct qdisc_util *qu, int argc, char **argv,
                             struct nlmsghdr *n, const char *dev)
{
    struct tc_bfifo_cc_qopt opt = {};
    int has_opt = 0;

    while (argc > 0) {
        if (strcmp(*argv, "limit") == 0) {
            NEXT_ARG();
            if (get_size(&opt.limit, *argv)) {
                fprintf(stderr, "bfifo_cc: invalid limit\n");
                return -1;
            }
            has_opt = 1;

        } else if (strcmp(*argv, "threshold") == 0) {
            NEXT_ARG();
            if (get_size(&opt.queue_control, *argv)) {
                fprintf(stderr, "bfifo_cc: invalid threshold\n");
                return -1;
            }
            has_opt = 1;

        } else {
            fprintf(stderr, "bfifo_cc: unknown argument '%s'\n", *argv);
            explain();
            return -1;
        }
        argc--;
        argv++;
    }

    if (has_opt)
        addattr_l(n, 1024, TCA_OPTIONS, &opt, sizeof(opt));

    return 0;
}
 

/*
 * bfifo_cc_print_opt: Prints the options for the bfifo_cc qdisc
 * qu: pointer to the qdisc_util structure
 * f: file pointer to print the options
 * opt: pointer to the rtattr structure that contains the options
 */
static int bfifo_cc_print_opt(const struct qdisc_util *qu, FILE *f,
                              struct rtattr *opt)
{
    struct tc_bfifo_cc_qopt *qopt;

    if (opt == NULL)
        return 0;

    if (RTA_PAYLOAD(opt) < sizeof(*qopt))
        return -1;

    qopt = RTA_DATA(opt);

    fprintf(f, "limit %u threshold %u",
            qopt->limit,
            qopt->queue_control);

    return 0;
    
    
    
    
    
    
    
    
    
    
}

struct qdisc_util bfifo_cc_qdisc_util = {
	.id = "bfifo_cc",
	.parse_qopt = bfifo_cc_parse_opt,
	.print_qopt = bfifo_cc_print_opt,
};
