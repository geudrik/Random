#! /usr/bin/env bash
#
# Pat Litke, inspired by Calomel (see Hat-Tip Below)
#
# License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   https://creativecommons.org/licenses/by-sa/4.0/
#
# Description: MegaPoop.sh is a collection of useful commands, lumped into a single script
#   for managing LSI RAID Cards (and their off-brand variants, like Dell PERCs)
#
# Hat-Tip: Calomel.org for being badass and providing a general layout to my version of their script.
#   Most of this script is theirs. I've gone through and made some changes, removed some
#   "useless" functionality, and added in some of my own. This variant suits my needs better than their base does.
#   https://calomel.org/megacli_lsi_commands.html

##
#### Set these variables
##

# Full path to the MegaCli64 Binary
MegaCli="/usr/local/sbin/MegaCli64"

# The enclosure number we're working in (defaults to 8)
#   If you are unsure, use "MegaCli64 -PDlist -a0 | grep "Enclosure Device"" to find out
ENCLOSURE="8"

##
#### Main
##

if [ $# -eq 0 ]; then

    echo ""
    echo "Usage: $0 [command] [options|help]"
    echo "============================================================================================="
    echo ""
    echo ""
    echo "  Informational Commands:"
    echo ""
    echo "status                               : Show status (health) of logical volumes"
    echo "drives                               : Show status (health) of all physical disks"
    echo "dinfo 'slot slot slot'               : Show detailed info on the listed disks"
    echo "progress                             : Show the progress ongoing rebuilds"
    echo "errors                               : Show drive errors"
    echo "bat                                  : Get battery health and capacity"
    echo "cardinfo                             : Dumps an exhaustive list of card settings/info"
    echo ""
    echo ""
    echo "  Management Commands:"
    echo ""
    echo "good [slot]                          : Marks a drive as \"Good\" (need slot number)"
    echo "batrelearn                           : Force the BBU into a re-learn cycle"
    echo "settime                              : Set the controllers datetime to system datetime"
    echo "replace [slot]                       : Replace a disk (neat slot number)"
    echo "expand [slot] [LogicalVOlume]        : Add a disk (grow) to an existing Raid6 Volume"
    echo "                                         Requires the logical volume number and a slot"
    echo "create 'slot slot slot'              : Create a Raid6 volume on Adapter 0 (default)"
    echo "                                         Requires a list of slots"
    echo ""
    echo ""
    echo "  Misc. Commands:"
    echo ""
    echo "cron 'email@domain.tld'              : Email alert on raid error (set up a cron for this)"
    echo "silence                              : Silences an alarm, but keeps it enabled globally"
    echo "defs                                 : Set a bunch of preferred default settings"
    echo "defsXtra                             : Set a few \"extra\" defaults (optional)"
    echo ""
    echo "Note: If you pass help as the second argument, an exhaustive description of what the"
    echo "      command does will be displayed."

    echo ""
    exit 0
fi

##
#### Begin
##

# Informational Commands
if [[ $1 == "status" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This command will output three chunks of information, separated by a string of dashes."
        echo "The first part is status information about the logical volumes the adapter handles,"
        echo "followed by patrol read settings and status, and consistency check progress"
        echo ""
        exit 1
    fi
    # Get logical disk information
    $MegaCli -LDInfo -Lall -aALL -NoLog
    echo "------------------------------------------------------------------------"
    # Get Patrol Read information
    $MegaCli -AdpPR -Info -aALL -NoLog
    echo "------------------------------------------------------------------------"
    # Get consistency check information
    $MegaCli -LDCC -ShowProg -LALL -aALL -NoLog
fi

if [[ $1 == "drives" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This command will show the status of all physical disks, describing whether they are"
        echo "on-line, missing, or just unconfigured."
        echo ""
        exit 1
    fi

    $MegaCli -PDlist -aALL -NoLog | egrep 'Slot|state|Device\ Id' | awk '/Slot/{if (x)print x;x="";}{x=(!x)?$0:x" -"$0;}END{print x;}' |sed "s/Firmware state:/Enclosure: $ENCLOSURE/g" |sed 's/-//g' | sed 's/Slot Number/Slot/g'|sort -k2 -n
fi

if [[ $1 == "dinfo" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Will show details of each disk passed as the second argument. Details include"
        echo "things like the disks capabilities, serial number, model number, SMART status, etc"
        echo ""
        exit 1
    fi

    BUILDER=$(LOL=''; for i in $2; do LOL="$LOL,$ENCLOSURE:$i"; done; echo ${LOL#?})
    $MegaCli -PdInfo -PhysDrv "[$BUILDER]" -a0
fi

if [[ $1 == "progress" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Like the short description says, this command shows the status and current completion"
        echo "progress of ongoing rebuilds."
        echo ""
        exit 1
    fi
    DRIVE=`$MegaCli -PDlist -aALL -NoLog | egrep 'Slot|state' | awk '/Slot/{if (x)print x;x="";}{x=(!x)?$0:x" -"$0;}END{print x;}' | sed 's/Firmware state://g' | egrep build | awk '{print $3}'`
    $MegaCli -PDRbld -ShowProg -PhysDrv [$ENCLOSURE:$DRIVE] -a0 -NoLog
fi

if [[ $1 == "errors" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This command will show all slots, followed by the number of detected errors."
        echo "If no errors are detected, only the slot number will be shown. Good for helping"
        echo "to determine if a drive should be replaced or not."
        echo ""
        exit 1
    fi
    echo "Slot Number: 0"; $MegaCli -PDlist -aALL -NoLog | egrep -i 'error|fail|slot' | egrep -v '0'
fi

if [[ $1 == "bat" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Shows the status of the BBU as well as the current charge. Not all that"
        echo "useful if you have a CacheVault or similar."
        echo ""
        exit 1
    fi
    $MegaCli -AdpBbuCmd -aAll -NoLog
fi

if [[ $1 == "cardinfo" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Shows all settings and information that the RAID card can provide."
        echo "This is a very exhaustive list."
        echo ""
        exit 1
    fi
    $MegaCli -AdpAllInfo -aAll -NoLog
fi

# Custodial Commands
if [[ $1 == "good" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "When a disk is first inserted, it may have old RAID headers. Given that these"
        echo "controllers are smart, if it smells foreign headers, it will essentially lock"
        echo "access to the disk. This method will change that, switching the disk status"
        echo "from \"Unconfigured(Bad)\" to \"Unconfigured(Good)\""
        echo ""
        echo "WARNING: THIS METHOD STRIPS FOREIGN HEADERS FROM THE DISK"
        echo ""
        exit 1
    fi
    $MegaCli -PDMakeGood -PhysDrv[$ENCLOSURE:$2] -a0 -NoLog
    $MegaCli -CfgForeign -Clear -aALL -NoLog
fi

if [[ $1 == "batrelearn" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This command forces the battery into a re-learn cycle."
        echo "This will tell the controller to let the battery discharge completely (0%)"
        echo "and then recharge, thereby helping to keep the Lithium based battery conditioned"
        echo ""
        echo "This may well take several hours or more to complete."
        echo ""
        echo "LSI recommends that a re-learn be done one every month or so."
        echo ""
        echo "If your caching policy is set to \"No Write Cache if Bad BBU\","
        echo "caching will be disabled during this relearn cycle for safety."
        echo "This means that writes to your array will be *VERY* slow (about 1/10th normal)"
        echo ""
        exit 1
    fi
    $MegaCli -AdpBbuCmd -BbuLearn -aALL -NoLog
fi

if [[ $1 == "settime" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Update the LSI RAID cards clock to match that of the current system time."
        echo "Consider running this once a day or so to keep your cards clock in sync."
        echo ""
        exit 1
    fi
    $MegaCli -AdpGetTime -aALL -NoLog
    $MegaCli -AdpSetTime `date +%Y%m%d` `date +%H:%M:%S` -aALL -NoLog
    $MegaCli -AdpGetTime -aALL -NoLog
fi

if [[ $1 == "replace" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This is a small collection of commands, designed to make replacing a drive easy."
        echo "We assume that you've made the physical replacement of the disk already."
        echo ""
        echo "1: Sets the status of the drive from Bad to Good"
        echo "2: Clears all foreign config information (preps it for import)"
        echo "3: Sets the disk as a Hot Spare. This SHOULD kick off an automatic rebuild"
        echo "4: Show rebuild progress"
        echo ""
        echo "WARNING: THIS WILL WIPE THE DISK YOU ARE REPLACING"
        echo ""
        exit 1
    fi
    logger "`hostname` - REPLACE enclosure $ENCLOSURE, drive $2 "
    # set Unconfigured(bad) to Unconfigured(good)
    $MegaCli -PDMakeGood -PhysDrv[$ENCLOSURE:$2] -a0 -NoLog
    # clear 'Foreign' flag or invalid raid header on replacement drive
    $MegaCli -CfgForeign -Clear -aALL -NoLog
    # set drive as hot spare
    $MegaCli -PDHSP -Set -PhysDrv [$ENCLOSURE:$2] -a0 -NoLog
    # show rebuild progress on replacement drive just to make sure it starts
    $MegaCli -PDRbld -ShowProg -PhysDrv [$ENCLOSURE:$2] -a0 -NoLog
fi

if [[ $1 == "grow" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Expand an existing Raid6 logical volume by 1 disk. This will take a very long time"
        echo "on systems that have large disks (and lots of them). You have been warned."
        echo ""
        exit 1
    fi
    logger "`hostname` - EXPAND enclosure $ENCLOSURE, drive $2, logical disk $3 "
    $MegaCli -LDRecon -Start -r6 -Add -Physdrv[$ENCLOSURE:$2] -L$3 -a0 -NoLog
    echo 1 > /sys/block/sda/device/rescan
fi

if [[ $1 == "create" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Create a Raid6 volume using the slots specified as the base disks. Further"
        echo "disks can be added in later, but the time required to grow a volume increases"
        echo "in a linear fashion for each disk added."
        echo ""
        exit 1
    fi

    logger "`hostname` - CREATE VOLUME enclosure $ENCLOSURE, slots $2"
    #TODO: This needs to be fixed. Currently the LOL creation loop doesn't generate the string properly
    BUILDER=$(LOL=''; for i in $2; do LOL="$LOL,$ENCLOSURE:$i"; done; echo ${LOL#?})
    echo "You are about to create a NEW logical volume using the following command"
    echo "Builder String: $MegaCli -CfgLdAdd -r6 \"[$BUILDER]\" -a0 -NoLog"
    read -r -p "Are you sure? [y/N] " response
    case $response in
        [yY][eE][sS]|[yY])
            ;;
        *)
            exit 1
            ;;
    esac
    $MegaCli -CfgLdAdd -r6 "[$BUILDER]" -a0 -NoLog
    echo 1 > /sys/block/sda/device/rescan
fi

# Misc. Commands
if [[ $1 == "cron" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "This command is designed to be run as a cron."
        echo ""
        echo "Periodically check for a degraded array and mail an alert out, passed as the second argument"
        echo "If you have your server in your house with the dreadful beep enabled, this is just an other"
        echo "avenue of notification."
        echo ""
        echo "However, if you have disabled the beep or your server is not near you, this may be your"
        echo "method of hearing about a failed/degraded disk."
        echo ""
        exit 1
    fi

    # Check if raid is in good condition
    STATUS=$($MegaCli -LDInfo -Lall -aALL -NoLog | egrep -i 'fail|degrad|error')
    TEMPFI="/tmp/ROFL.XXXXXXXX"

    # We have a failed/degraded/error'd logical volume
    if [ "$STATUS" ]; then

        # We HAVE a pre-determined failed file. Use it
        if [ -f /tmp/ROFL.XXXXXXXX ]; then

            # Get epoch of last modified time of our temp file
            TMPSTAT=$(date --utc --reference=$TEMPFI +%s)
            # Get NOW() epoch
            NOW=$(date +%s)
            DELTA=$(($NOW-$TMPSTAT))

            # We still have an issue, and our temp file timestamp is older than 24 hours, send new email
            if [ $DELTA -gt 86400 ]; then
                cat $TEMPFI |mail -s `hostname`' - RAID Notification' $2
                # Update the modified time on our lock file
                touch $TEMPFI
            fi
        # Assume we do not have a file
        else
            $MegaCli -PDlist -aALL -NoLog | egrep 'Slot|state' | awk '/Slot/{if (x)print x;x="";}{x=(!x)?$0:x" -"$0;}END{print x;}' | sed 's/Firmware state://g' |sort -k3 -n |tee $TEMPFI |mail -s `hostname`' - RAID Notification' $2
        fi

    # We have no status. Make sure we're cleaning up after ourselves
    else
        if [ -f $TEMPFI ]; then
            rm $TEMPFI
        fi
    fi
fi


if [[ $1 == "silence" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Silence the alarm if it's going off. This will not actually disable the alarm"
        echo "on the card, rather just turn off the beeping for the most recent event that"
        echo "triggered it."
        echo ""
        exit 1
    fi
    $MegaCli -AdpSetProp AlarmSilence -a0
fi

if [[ $1 == "defs" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "Set up the RAID card to handle volumes in the most efficient means possible."
        echo "This assumes that you have a BBU at least."
        echo ""
        echo "The following defaults will be set:"
        echo "1: Read-Cache enabled - All reads will be buffered into memory"
        echo "2: Adaptive Read-Ahead will be enabled"
        echo "3: Enable internal caching"
        echo "4: Enable Write-Back caching"
        echo "5: Continue booting with data stuck in cache"
        echo "6: Run a PATROL every month (672 Hours)"
        echo "7: Check consistency once a month (672 Hours)"
        echo "8: Enable autobuild when a new drive is inserted and/or set as a hot spare"
        echo "9: Set RAID rebuild rate to 60%"
        echo "10: Set RAID consistency check to 60% (fast parity checking)"
        echo "11: Enable native command queuing (NCQ) on all disks"
        echo ""
        echo "* WARNING: You will lose data if the machine loses power and you either"
        echo "  do not have a BBU (or equivalent), or it's faulted. You have been warned"
        echo ""
        exit 1
    fi
    # Read Cache enabled specifies that all reads are buffered in cache memory.
    $MegaCli -LDSetProp -Cached -LAll -aAll -NoLog
    # Adaptive Read-Ahead if the controller receives several requests to sequential sectors
    $MegaCli -LDSetProp ADRA -LALL -aALL -NoLog
    # Hard Disk cache policy enabled allowing the drive to use internal caching too
    $MegaCli -LDSetProp EnDskCache -LAll -aAll -NoLog
    # Write-Back cache enabled
    $MegaCli -LDSetProp WB -LALL -aALL -NoLog
    # Continue booting with data stuck in cache. Set Boot with Pinned Cache Enabled.
    $MegaCli -AdpSetProp -BootWithPinnedCache -1 -aALL -NoLog
    # PATROL run every 672 hours or monthly (RAID6 77TB @60% rebuild takes 21 hours)
    $MegaCli -AdpPR -SetDelay 672 -aALL -NoLog
    # Check Consistency every 672 hours or monthly
    $MegaCli -AdpCcSched -SetDelay 672 -aALL -NoLog
    # Enable autobuild when a new Unconfigured(good) drive is inserted or set to hot spare
    $MegaCli -AdpAutoRbld -Enbl -a0 -NoLog
    # RAID rebuild rate to 60% (build quick before another failure)
    $MegaCli -AdpSetProp \{RebuildRate -60\} -aALL -NoLog
    # RAID check consistency rate to 60% (fast parity checks)
    $MegaCli -AdpSetProp \{CCRate -60\} -aALL -NoLog
    # Enable Native Command Queue (NCQ) on all drives
    $MegaCli -AdpSetProp NCQEnbl -aAll -NoLog
fi

if [[ $1 == "defsXtra" ]]; then
    if [[ $2 == "help" ]]; then
        echo ""
        echo "These are extra defaults that may or may not be useful to you."
        echo ""
        echo "1: Disable the audible alarm (not useful in a server room)"
        echo "2: *Enable Write-Back Cache, even if BBU is faulted"
        echo "3: Disable Auto-Relearn of the BBU (should be set for a monthly cron)"
        echo ""
        exit 1
    fi
    # Sound alarm disabled (server room is too loud anyways)
    $MegaCli -AdpSetProp AlarmDsbl -aALL -NoLog
    # Use write-back cache mode even if BBU is bad. Make sure your machine is on UPS too.
    $MegaCli -LDSetProp CachedBadBBU -LAll -aAll -NoLog
    # Disable auto learn BBU check which can severely affect raid speeds
    OUTBBU=$(mktemp /tmp/output.XXXXXXXXXX)
    echo "autoLearnMode=1" > $OUTBBU
    $MegaCli -AdpBbuCmd -SetBbuProperties -f $OUTBBU -aALL -NoLog
    rm -rf $OUTBBU
fi

exit 0
