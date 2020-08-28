# forms_webhook
This provides a webhook which Typeforms can call. It parses the username and requested group from the payload, adds the user to the 506 group using the Discourse API, and notifies the admin via email. It starts automatically as a service on the Lightsail instance.
