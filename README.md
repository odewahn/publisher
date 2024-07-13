# Loading content to portal

https://cdn.oreillystatic.com/safari-submission-guides/portal/book.html
https://cdn.oreillystatic.com/safari-submission-guides/video/book.html
https://cdn.oreillystatic.com/safari-submission-guides/book/book.html

We also have this integration tests repo that has examples of incoming test files in case you’d want to check out the xml format mentioned in those guides: https://github.com/oreillymedia/content_ingestion_integration_tests/tree/main/uptime_test/test_files

For example this is a valid book xml: https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/test_files/book/standard/9781492076803.xml

we just included this section within the video guide because audiobooks are otherwise identical to videos: https://cdn.oreillystatic.com/safari-submission-guides/video/book.html#audio-only-support-PasQupt0

# Loading content from APIs

- [ConEng Dev Cheat Sheet](https://docs.google.com/document/d/1xx0qkYvOxtUI-seeC_vAU9nhuPjVeZYJyLBKCdKEdqw/edit#) has a bunch of great information on how things work

- End to end overview of content process - https://drive.google.com/file/d/1u15FDLIfJjRJWpKnL7Wo2eZu_PRmNbSk/view

(From Cris Pope)

media storage client: This is the library many of our services use to interact with our Google Cloud buckets. It has lots of helper methods to upload and download files. You could use it if you decide to send us GCP links instead of CDN ones. https://github.com/oreillymedia/media-storage-client

Content Submission Service: This service gets submissions in onix format and files dropped to our FTP and uploads them to GCP using the media client, and makes a json payload to submit to ingestion with those links. It uses the same API TRIM uses and that your service would use. So this the closest example we have for you. https://github.com/oreillymedia/content-submission-service

It submits to cowbird here: https://github.com/oreillymedia/content-submission-service/blob/main/ingestion/tasks.py#L121.

And this is a test that shows an expected payload: https://github.com/oreillymedia/content-submission-service/blob/main/ingestion/tests/test_tasks.py#L121

Integrations service and miso delivery service: These are examples of simple services we made to deliver content to external clients. Both consume messages with metadata from the item, then process that in a task that makes a json payload to then deliver it. So it is similar to your case where you need to get a data input and output a json payload and deliver it by POST (to external clients, not to ingestion like the submission service). https://github.com/oreillymedia/integrations-service and https://github.com/oreillymedia/miso-delivery-service

This is an integrations test service we have to send automated test that has some test payloads we send in to cowbird to test TRIM, you can use them as example payloads too:

live event series: https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/upti[…]test_files/live-event-series/standard_series/0636920431657.json

live event: https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/test_files/live-event/standard_event/0636920431658.json

Once you start testing and posting items to us in dev-gke, you can go to this cowbird submission list page and see if your submission is submitted or if it failed QA. If it failed, you can click on the item and see under errors why it failed. https://cowbird.platform.gcp.oreilly.review/admin/portal/safariportalsubmission/ (you can log in with unified auth)

Ingesting into cowbird via the API:

This is the view you would post and patch to https://github.com/oreillymedia/cowbird/blob/main/portal/api/views.py#L44 and https://github.com/oreillymedia/cowbird/blob/main/portal/api/views.py#L57.
The URL is http://http.cowbird.svc.cluster.local/api/v1/submissions/.
Here are some test examples: https://github.com/oreillymedia/cowbird/blob/main/portal/api/tests/test_views.py#L176

# Notes from Content Ingestion 101

4 ways content can be submitted:

- FTP
- Portal UI
- HTTP Posts to Cowbird API
- Directly loaded into a downstream service

## Creating a publisher

You login to the publisher data service here:

https://publisherdataservice.platform.gcp.oreilly.review/admin/login/?next=/admin/

You can create a new publisher (I call mine "ANO Press"). The description should look like this:

```
{  "text/html": "<span>Test publisher for ehanced books projects</span>",
   "text/plain": "Test publisher for enhanced books project"
}
```

Set the Cda Licensors to `O'Reilly Media`

You can see the publisher page here:

https://learning.oreilly.review/publisher/<uuid>/

This will redirect you to a URL with the slugified name:

https://learning.oreilly.review/publisher/ano-press/

You can also set your uploader credentials. I creaed one called `ANO` (not that you're limited to 3 characters here for some reason!) with the username `anopress` and password `password123`

Note that these credentials are used to set FTP credentials and login credentials for Portal.

By default your new publisher isn't whitelisted:

https://cowbird.platform.gcp.oreilly.review/admin/portal/publisher/418/change/

Someone from Digidist could explain this better than me, but when we sign new publishers (or we have troubles with an existing publisher) they have `is_whitelisted` set to false, and each submission needs to be manually approved by a human. When the relationship with the publisher progresses/improves, digidist sets that field to true and submissions automatically flow through the system.

### Portal Access

Go here and login with your credentials:

```
https://cowbird.platform.gcp.oreilly.review/safari-portal/
```

Enter all the metadata (be sure to use at least 13 characters in he identifier!!!). You can then follow along with the ingestion process in:

https://ingestion-monitoring-service.platform.gcp.oreilly.review/admin/product-status/66666TESTANO

https://ingestion-monitoring-service.platform.gcp.oreilly.review/admin/product-status/66666TEST123

https://cowbird.platform.gcp.oreilly.review/admin/portal/safariportalsubmission/

## Force a reload of a book to QA

We have a special Jenkins job for this at https://jenkins.common-build.gcp.oreilly.com/job/MetaCon/job/tools/job/send-product-to-qa/

- Click Build with Parameters from the left
- Enter the identifier of the work. (Note this is the fpid style identifier like 9781449329129 not the ourn)
- Click build!

Caveats:

- This only works with content types that go through “normal” ingestion (so this won’t work with a certification guide)
- The normal ingestion checks apply which can cause failures not visible in the Jenkins job. (We occasionally get old content with a too small cover image, for example.)
- Depending on the size of the work being copied it can take a while to show up on the QA site. (We still need to upload videos to Kaltura, process epubs, etc)
- Generally if something isn’t showing up within a hour just ping metacon and someone can take a look

# Content Discovery notes

This project shows the XML used for ingestion for all content types and then how it's used across all APIs. For discovery, there is a section in the XML called [safari-classification](https://cdn.oreillystatic.com/safari-submission-guides/video/book.html#andltsafari-classificationandgt-q8swFVhd):

```
  <safari-classification>
    <class scheme="safari-video-classification">course</class>
  </safari-classification>
```

You can look in the `expected_results` folder of the appropriate content type in [https://github.com/oreillymedia/content_ingestion_integration_tests/] to see how use this value is used across a variety of APIs. (The easist way to do this is probbaly to download the repo and use grep if you're doing it a lot.)

In poking around, is seems that `safari-classification` is used to populate the `tags` element in `ard_service_v2.json` endpoint:

https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/test_files/video/audiobook_with_audioonly/expected_results/card_service_v2.json#L40-L42

```
   "tags": [
      "course"
   ],
```

https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/test_files/video/audiobook_with_audioonly/9781492054542.xml#L38-L40

These are then dicoverable in the metadata card service, as documented in:

https://github.com/oreillymedia/card-service/blob/main/docs/card_service.apib

So, to find all courses, you could use this if you are on the network/inside the firewall:

https://api.oreilly.com/api/v2/metadata/?tag=course

There is a publicly available API for customr integrations that you can use off the network:

https://api.oreilly.com/api/v1/integrations/content/?tag=shortcut

## You can create multiple tags

https://oreilly.slack.com/archives/C018Z6TQDQF/p1719418345133259

 <safari-classification>
    <class scheme="safari-video-classification">thing1</class>
    <class scheme="safari-video-classification">thing2</class>
  </safari-classification>

The xml example above with 2 tags would become and array of tags: ['thing1', thing2'] after ingestion. The catch is that you need to use authorized tags which you can see a list of here: https://cowbird.platform.gcp.oreilly.com/admin/portal/tag/

The API query would be like this: https://api.oreilly.com/api/v1/integrations/content/?tag=conference&tag=structured-learning, or https://api.oreilly.com/api/v1/integrations/content/?tag=thing1&tag=thing2 in this case. That gives you items with either one of the tags.

### Setting tags and metadata for existing work

here is the documentation on how to use the API. Once you send something in, you will be able to see it (and any errors) under the portal or portal in cowbird admin. https://github.com/oreillymedia/cowbird/blob/main/docs/portal.apib

Cris Pope
:spiral_calendar_pad: < 1 minute ago

In the content integration tests repo you mentioned above, we have test cases for live events and live event series which are posted to us using the API, so you can use them as examples too:

https://github.com/oreillymedia/content_ingestion_integration_tests/tree/main/uptime_test/test_files
https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/upti[…]test_files/live-event-series/standard_series/0636920431657.json

0636920431657.json
<https://github.com/oreillymedia/content_ingestion_integration_tests|oreillymedia/content_ingestion_integration_tests>oreillymedia/content_ingestion_integration_tests | Added by GitHub

Cris Pope
:spiral_calendar_pad: < 1 minute ago

Our audiobooks are now being submitted to us using the API as well so here's an example of a video post: https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/test_files/video/standard_json_post/0636920363026.json

Here's an example of how to post to the API to update metadata:

https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/api.py

## To build:

```
pyinstaller --noconfirm --clean publisher.spec
```

## To package, sign, and notarize

This tool does all the steps in a nice package:

https://github.com/txoof/codesign

Note that I renamed it `pycodesign` when I downloaded it, even though it's called `pycodesign.py` when you download it from the repo.

```
cd dist
pycodesign ../pycodesign.ini
```

# SFTP Ingestion notes

We switched from plain old ftp to sftp, which requires using a library that supports it. We use paramiko.

https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/content_ingestion_integration_tests/settings.py#L39
is where settigs are (but no password)

and then for code

https://github.com/oreillymedia/content_ingestion_integration_tests/blob/main/uptime_test/ftp.py

Other docs/tutorial links:

- https://www.linode.com/docs/guides/use-paramiko-python-to-ssh-into-a-server/
