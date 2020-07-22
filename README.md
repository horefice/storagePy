[![Build Status](https://travis-ci.org/horefice/storagePy.svg?branch=master)](https://travis-ci.org/horefice/storagePy)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)

# storagePy

With StoragePy you can instantly have a testing platform for your JSONs. That is, a solid RESTfull API + DB waits for you!

## Index

* [Getting Started](#getting-started)
* [Requests](#requests)
* [Limitations](#limitations)
* [License](#license)

## Getting Started

For using the API you must first sign up and get a valid username.
Only an email address is required for signing up.

Users can sign up through:

* [Official Website](http://storagepy.tk)
* Post request

One's username is calculated MD5-hashing his/her email address. <br>
If you lose your username, you can still calculate it or sign up again (no data will be lost, I swear). <br>

### Signing up at the official website

Enter you email into the appropriate field at the beggining of the page. <br>
You will receive an alert containing your assigned username as response. And that's it!

### Signing up using `POST`

Using a post request containing your email is enough for signing up.
All you need to do is:

* Prepare a `POST` request to `http://api.storagepy.tk/signup`
* Add `content-Type: "application/x-www-form-urlencoded"` to headers
* Set `email=your_email` as data
* Don't worry about `Access-Control-Allow-Origin`
* Wait for a 201 response containing `{ "hash" : username }`

The response above means you're done and the server is ready for you.

**Sample request:**

```shell
curl -X POST -H "Content-Type:application/x-www-form-urlencoded" -d 'email=johnsnow%40gmail.com' http://api.storagepy.tk/signup
```

### Is it safe?

The only personal information we store is your email address. Since we hash it for signing up, anyone with access to your username will not be able to recover your email address. Besides that, we do not encourage you to put any sensitive data on our databases, it's a testing platform!

## Requests

All the requests must fulfill the following requirements:
* Have `http://api.storagepy.tk/` as the base url.
* Expect a response in `JSON` format.
* Send data (if applicable) in `JSON` format.

### Get data

  Returns json data from the specified user.

* **URL**

  /:user_id

* **Method:**

  `GET`
  
*  **URL Params**
 
   `user_id=[32-byte hex-string]`

* **Data Params**

  None

* **Success Response:**

  * **Code:** 200 <br>
    **Content:** `{ 'data' : your_data_as_json }`
 
* **Error Response:**

  * **Code:** 404 NOT FOUND <br>
    **Content:** `{ 'error' : 'Not found' }`

  OR

  * **Code:** 400 BAD REQUEST <br>
    **Content:** `{ 'error' : 'Bad request' }`

* **Sample Call:**

  ```javascript
    $.ajax({
      url: "/d41d8cd98f00b204e9800998ecf8427e",
      type : "GET",
      success : function(r) {
        console.log(r);
      }
    });
  ```

### Insert or update data

  Inserts or updates data from the specified user. Returns new data.

* **URL**

  /:user_id

* **Method:**

  `POST` or `PUT`
  
*  **URL Params**
 
   `user_id=[32-byte hex-string]`

* **Data Params**

  `your_data_as_json`

* **Success Response:**

  * **Code:** 200 `PUT` || 201 `POST` <br>
    **Content:** `{ 'data' : your_data_as_json }`
 
* **Error Response:**

  * **Code:** 404 NOT FOUND <br>
    **Content:** `{ 'error' : 'Not found' }`

  OR

  * **Code:** 400 BAD REQUEST <br>
    **Content:** `{ 'error' : 'Bad request' }`

  OR

  * **Code:** 413 PAYLOAD TOO LARGE <br>
    **Content:** `{ 'error' : 'Payload too large' }`

* **Sample Call:**

  ```javascript
    your_data_as_json = JSON.stringify(your_data)
    
    $.ajax({
      url: "/d41d8cd98f00b204e9800998ecf8427e",
      type : "POST", // POST || PUT
      contentType: "application/json",
      data: your_data_as_json
      success : function(r) {
        console.log(r);
      }
    });
  ```

### Delete data

  Delete data from the specified user. Returns `true` if succeeded.

* **URL**

  /:user_id

* **Method:**

  `DELETE`
  
*  **URL Params**
 
   `user_id=[32-byte hex-string]`

* **Data Params**

  None

* **Success Response:**

  * **Code:** 200 <br>
    **Content:** `{ 'result' : true }`
 
* **Error Response:**

  * **Code:** 404 NOT FOUND <br>
    **Content:** `{ 'error' : 'Not found' }`

  OR

  * **Code:** 400 BAD REQUEST <br>
    **Content:** `{ 'error' : 'Bad request' }`

* **Sample Call:**

  ```javascript
    $.ajax({
      url: "/d41d8cd98f00b204e9800998ecf8427e",
      type : "DELETE",
      success : function(r) {
        console.log(r);
      }
    });
  ```

## Limitations

We believe our users will make a fair use of the platform. Therefore, each user has a really high quota for requests and a 5mb quota for storage.

## License

[MIT License](LICENSE.md)