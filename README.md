## `strava`

This repository implements a simple library for interacting with the Strava API, and some higher-level scripts that utilize it to automate routine tasks.

### Authentication

The client supports authentication via access token, or via more persistent variables: `client_id`, `client_secret`, and `refresh_token`.

The first two of these are available in your Strava [profile](https://www.strava.com/settings/api). The `refresh_token` is also available there, but not with sufficient permissions to query activities. For this reason, we need to do a little extra work to generate a `refresh_token` that is suitable for querying activities.

**Persistent Credentials**

Grab the persistent credentials directly from your [profile](https://www.strava.com/settings/api) and add them to the environment. 

```bash
export CLIENT_ID=<...>
export CLIENT_SECRET=<...>
```

**Obtaining a Refresh Token**

Get an authorization code:

```bash
# generate the url
echo "https://www.strava.com/oauth/authorize?client_id=$CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all"
```

Then visit this URL in the browser. Grab the code from the URL and add it to the environment.

```bash
export CODE=9cf499438877cba789916c5adab81d279f9836cb
```

Now, we can request a refresh token with the proper authorizations:

```bash
curl --request POST \
  --url "https://www.strava.com/oauth/token?client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&code=$CODE&grant_type=authorization_code"
```

The token appears in the field `refresh_token`.

```bash
export REFRESH_TOKEN=636d4c29736fb88a7eb36677be20e22a6394e938
```

### Acknowledgements

This implementation was inspired by the work [zwinslett](https://github.com/zwinslett) on [strava-zone-aggregator](https://github.com/zwinslett/strava-zone-aggregator/tree/main).
