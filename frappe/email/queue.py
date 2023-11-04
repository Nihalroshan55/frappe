# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr, get_url, now_datetime
from frappe.utils.verified_command import get_signed_params, verify_request

# After this percent of failures in every batch, entire batch is aborted.
# This usually indicates a systemic failure so we shouldn't keep trying to send emails.
EMAIL_QUEUE_BATCH_FAILURE_THRESHOLD_PERCENT = 0.33
EMAIL_QUEUE_BATCH_FAILURE_THRESHOLD_COUNT = 10


def get_emails_sent_this_month(email_account=None):
	"""Get count of emails sent from a specific email account.

	:param email_account: name of the email account used to send mail

	if email_account=None, email account filter is not applied while counting
	"""
	q = """
		SELECT
			COUNT(*)
		FROM
			`tabEmail Queue`
		WHERE
			`status`='Sent'
			AND
			EXTRACT(YEAR_MONTH FROM `creation`) = EXTRACT(YEAR_MONTH FROM NOW())
	"""

	q_args = {}
	if email_account is not None:
		if email_account:
			q += " AND email_account = %(email_account)s"
			q_args["email_account"] = email_account
		else:
			q += " AND (email_account is null OR email_account='')"

	return frappe.db.sql(q, q_args)[0][0]


def get_emails_sent_today(email_account=None):
	"""Get count of emails sent from a specific email account.

	:param email_account: name of the email account used to send mail

	if email_account=None, email account filter is not applied while counting
	"""
	q = """
		SELECT
			COUNT(`name`)
		FROM
			`tabEmail Queue`
		WHERE
			`status` in ('Sent', 'Not Sent', 'Sending')
			AND
			`creation` > (NOW() - INTERVAL '24' HOUR)
	"""

	q_args = {}
	if email_account is not None:
		if email_account:
			q += " AND email_account = %(email_account)s"
			q_args["email_account"] = email_account
		else:
			q += " AND (email_account is null OR email_account='')"

	return frappe.db.sql(q, q_args)[0][0]


def get_unsubscribe_message(unsubscribe_message: str, expose_recipients: str) -> "frappe._dict[str, str]":
	unsubscribe_message = unsubscribe_message or _("Unsubscribe")
	unsubscribe_link = f'<a href="<!--unsubscribe_url-->" target="_blank">{unsubscribe_message}</a>'
	unsubscribe_html = _("{0} to stop receiving emails of this type").format(unsubscribe_link)
	html = f"""<div class="email-unsubscribe">
			<!--cc_message-->
			<div>
				{unsubscribe_html}
			</div>
		</div>"""

	text = f"\n\n{unsubscribe_message}: <!--unsubscribe_url-->\n"
	if expose_recipients == "footer":
		text = f"\n<!--cc_message-->{text}"

	return frappe._dict(html=html, text=text)


def get_unsubcribed_url(reference_doctype, reference_name, email, unsubscribe_method, unsubscribe_params):
	params = {
		"email": cstr(email),
		"doctype": cstr(reference_doctype),
		"name": cstr(reference_name),
	}
	if unsubscribe_params:
		params.update(unsubscribe_params)

	query_string = get_signed_params(params)

	# for test
	frappe.local.flags.signed_query_string = query_string

	return get_url(unsubscribe_method + "?" + get_signed_params(params))


@frappe.whitelist(allow_guest=True)
def unsubscribe(doctype, name, email):
	# unsubsribe from comments and communications
	if not frappe.flags.in_test and not verify_request():
		return

	try:
		frappe.get_doc(
			{
				"doctype": "Email Unsubscribe",
				"email": email,
				"reference_doctype": doctype,
				"reference_name": name,
			}
		).insert(ignore_permissions=True)

	except frappe.DuplicateEntryError:
		frappe.db.rollback()

	else:
		frappe.db.commit()

	return_unsubscribed_page(email, doctype, name)


def return_unsubscribed_page(email, doctype, name):
	frappe.respond_as_web_page(
		_("Unsubscribed"),
		_("{0} has left the conversation in {1} {2}").format(email, _(doctype), name),
		indicator_color="green",
	)


def flush():
<<<<<<< HEAD
	"""flush email queue, every time: called from scheduler"""
	from frappe.email.doctype.email_queue.email_queue import send_mail
	from frappe.utils.background_jobs import get_jobs
=======
	"""flush email queue, every time: called from scheduler.

	This should not be called outside of background jobs.
	"""
	from frappe.email.doctype.email_queue.email_queue import EmailQueue
>>>>>>> d5d0dfb58b (perf: Reuse SMTP connection when flushing email queue)

	# To avoid running jobs inside unit tests
	if frappe.are_emails_muted():
		msgprint(_("Emails are muted"))

	if cint(frappe.db.get_default("suspend_email_queue")) == 1:
		return

<<<<<<< HEAD
	try:
		queued_jobs = set(get_jobs(site=frappe.local.site, key="job_name")[frappe.local.site])
	except Exception:
		queued_jobs = set()

	for row in get_queue():
		try:
			job_name = f"email_queue_sendmail_{row.name}"
			if job_name not in queued_jobs:
				frappe.enqueue(
					method=send_mail,
					email_queue_name=row.name,
					now=from_test,
					job_name=job_name,
					queue="short",
				)
			else:
				frappe.logger().debug(f"Not queueing job {job_name} because it is in queue already")
=======
	email_queue_batch = get_queue()
	if not email_queue_batch:
		return

	failed_email_queues = []
	for row in email_queue_batch:
		try:
<<<<<<< HEAD
<<<<<<< HEAD
			send_mail(
				email_queue_name=row.name,
				now=from_test,
				job_id=f"email_queue_sendmail_{row.name}",
				queue="short",
				deduplicate=True,
			)
>>>>>>> 050c0b26f8 (fix: flush emails from single background jobs)
=======
			send_mail(email_queue_name=row.name)
>>>>>>> 4e318a0280 (fix: Abort flushing email queue if >50% fail.)
=======
			email_queue: EmailQueue = frappe.get_doc("Email Queue", row.name)
<<<<<<< HEAD
			smtp_server_instance = email_queue.get_email_account().get_smtp_server()
			opened_connections.add(smtp_server_instance)
			email_queue.send(smtp_server_instance=smtp_server_instance)
>>>>>>> d5d0dfb58b (perf: Reuse SMTP connection when flushing email queue)
=======
			email_queue.send()
>>>>>>> a4382fda5a (fix: Automatically close SMTP connections on exit)
		except Exception:
			frappe.get_doc("Email Queue", row.name).log_error()
			failed_email_queues.append(row.name)

			if (
				len(failed_email_queues) / len(email_queue_batch) > EMAIL_QUEUE_BATCH_FAILURE_THRESHOLD_PERCENT
				and len(failed_email_queues) > EMAIL_QUEUE_BATCH_FAILURE_THRESHOLD_COUNT
			):
				frappe.throw(_("Email Queue flushing aborted due to too many failures."))


def get_queue():
	batch_size = cint(frappe.conf.email_queue_batch_size) or 500

	return frappe.db.sql(
		f"""select
			name, sender
		from
			`tabEmail Queue`
		where
			(status='Not Sent' or status='Partially Sent') and
			(send_after is null or send_after < %(now)s)
		order
			by priority desc, retry asc, creation asc
		limit {batch_size}""",
		{"now": now_datetime()},
		as_dict=True,
	)


def set_expiry_for_email_queue():
	"""Mark emails as expire that has not sent for 7 days.
	Called daily via scheduler.
	"""

	frappe.db.sql(
		"""
		UPDATE `tabEmail Queue`
		SET `status`='Expired'
		WHERE `modified` < (NOW() - INTERVAL '7' DAY)
		AND `status`='Not Sent'
		AND (`send_after` IS NULL OR `send_after` < %(now)s)""",
		{"now": now_datetime()},
	)
