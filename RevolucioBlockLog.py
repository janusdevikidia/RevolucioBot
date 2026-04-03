# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import time
import traceback

import pywikibot
from urllib.error import HTTPError

from includes.wiki import get_wiki
from version import ver

arg = argparse.ArgumentParser()
required_arg = arg.add_argument_group("required arguments")
required_arg.add_argument("--wiki", required=True)
required_arg.add_argument("--lang", required=True)
arg.add_argument("--user")
required_arg.add_argument("--limit", type=int, required=True)
args = arg.parse_args()

if __name__ == "__main__":
    pywikibot.output("Revolució %s - Block Log Monitor" % ver)

    if args.wiki != "vikidia" or args.lang != "fr":
        pywikibot.output("La surveillance du journal des blocages n'est disponible que pour fr.vikidia. Abandon.")
        exit(0)

    if not os.path.exists("files"):
        os.mkdir("files")
    os.chdir("files")

    if args.user is not None:
        site = get_wiki(args.wiki, args.lang, args.user)
    else:
        site = get_wiki(args.wiki, args.lang, "RevolucioBot")

    # Timestamp de départ : on remonte de --limit secondes dans le passé
    timestamp = str((datetime.datetime.now() - datetime.timedelta(seconds=args.limit)).timestamp())

    pywikibot.output("Récupération du journal des blocages...")
    status_ok = False
    while not status_ok:
        try:
            blocked_users = site.get_block_log(timestamp)
            status_ok = True
        except HTTPError:
            pywikibot.error(traceback.format_exc())
            pywikibot.error("Erreur de connexion. Nouvel essai dans 10 secondes...")
            time.sleep(10)

    if not blocked_users:
        pywikibot.output("Aucun blocage trouvé dans la période.")
    else:
        pywikibot.output("%d utilisateur(s) bloqué(s) : %s" % (len(blocked_users), ", ".join(blocked_users)))

    # Page d'alerte du jour courant
    alert_page_tpl = site.config.get("alert_page")
    if alert_page_tpl:
        alert_page_name = datetime.datetime.now().strftime(
            alert_page_tpl.replace("\r", "").replace("\n", "")
        )
    else:
        alert_page_name = "Project:Alerte"

    pywikibot.output("Page d'alerte cible : %s" % alert_page_name)

    for username in blocked_users:
        status_ok = False
        while not status_ok:
            try:
                pywikibot.output("Vérification de la demande pour : %s" % username)
                modified = site.mark_admin_request_done(username, alert_page_name)
                if modified:
                    pywikibot.output("Demande marquée comme faite pour : %s" % username)
                else:
                    pywikibot.output("Aucune demande en attente trouvée pour : %s" % username)
                status_ok = True
            except HTTPError:
                pywikibot.error(traceback.format_exc())
                pywikibot.error("Erreur de connexion. Nouvel essai dans 10 secondes...")
                time.sleep(10)
            except Exception:
                pywikibot.error(traceback.format_exc())
                status_ok = True

    pywikibot.output("Surveillance du journal des blocages terminée.")
