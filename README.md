# Paper Downloader
If you want to download all papers of a conference, or a single PDF containing the first pages of all papers for a quick glance of the papers, this tool is exactly made for you.

**Given the URL of the conference webpage** which contains the list of accepted papers (e.g., the webpage of the accepted papers or the program), it can:

* **Automatically extract paper titles**
* **Search over Internet for their PDF files**
* **Download the PDFs**
* **Merge your specified pages into a single PDF**

If you don't need the automatic paper title extraction feature, you can also just give it a list of paper titles/URLs, and it can download/merge the PDFs for you.

## Install
```
git clone --recurse-submodules https://github.com/fjxmlzn/paper_downloader.git
```

## Quick examples
Before running these examples, you may want to [setup cookie and user agent](#cookie) first.

### Example 1
```
python pd.py -u https://www.usenix.org/conference/nsdi19/technical-sessions --store --merge 1 --merge 2
```
Here,

* `-u https://www.usenix.org/conference/nsdi19/technical-sessions`: this is the webpage of NSDI 2019, with a list of all accepted papers
* `--store`: downloading all papers into `pdf` folder
* `--merge 1 --merge 2`: extracting the first and the second page of all papers into a single PDF `pdf/merged.pdf`. You can specify any page to be merged using single or multiple `--merge`

### Example 2
```
python pd.py -c nsdi2019 -u https://www.usenix.org/conference/nsdi19/technical-sessions --store --merge 1 --merge 2
```
The only difference is the additional option `-c nsdi2019`. This will save the following intermediate results:

*  `conf_url/nsdi2019.conf_url.json`: this contains the URL of the conference webpage and the HTML indicators for paper titles that are automatically detected by the tool. See [troubleshooting](#troubleshooting) and [how it works](#how-it-works) for more details
*  `conf_url/nsdi2019.paper_list.json`: this contains the list of detected paper titles
*  `conf_url/nsdi2019.pdf_url.json`: this contains the PDF links of the papers

Next time when you run the tool, you do not need to specify `-u`, i.e.

```
python pd.py -c nsdi2019 --store --merge 1 --merge 2
```

is enough. It will 

* Use `conf_url/nsdi2019.pdf_url.json` if exists. Otherwise,
* Use `conf_url/nsdi2019.paper_list.json` if exists, to generate  `conf_url/nsdi2019.pdf_url.json`. Otherwise,
* Use `conf_url/nsdi2019.conf_url.json` if exists, to generate the other two.

Those files are important for [troubleshooting](#troubleshooting), and you are welcome to [upload these files to the repo](#contributing). Click these links for the details.

### Prefetched conference
`./conf_url/` contains prefetched paper list of several conferences (e.g., NSDI, SIGCOMM, IMC) using this tool. For these conferences, you don't need to worry about the problems in [troubleshooting](#troubleshooting). You can directly specify conference name to download and merge papers (e.g., `python pd.py -c nsdi2019 --store --merge 1 --merge 2`). You are welcome to upload the paper list of your favorite conferences to this repo to help others. See [here](#contributing) for details.

## Troubleshooting
The tool is designed to reduce your manual work as much as possible. However, there are cases where you might need to manually tune it.

In the following description, `<>` means the conference name you specified through `-c`.

### `<>.paper_list.json` does not contain the correct paper titles
To get a sense of the following solutions, you may want to look at [how it works](#how-it-works) first.

Here are some possible ways to fix it.

> Before you try either solution, you should delete `<>.paper_list.json` and `<>.pdf_url.json`, so that the tool will try to fetch the paper list again.

* Add `--debug` option when running it. The tool will generate `debug.txt`. You will see many sections separated by `---`. If you find a section containing all the desired paper titles, add the indicator string to the `*.conf_url.json` file, according to the instruction at the beginning of the section.
* If in the above step, you find that there is a section containing the paper titles but also some other random strings, you may want to try adding `-a class` option (or other HTML tag properties) when running the tool. To see what it means, please read [how it works](#how-it-works).

In most cases we have tried, the above two ways can give you a reasonably correct list of paper titles. If there are still some errors, you can manually modify `<>.paper_list.json`.

### PDF links of some/all papers in `<>.pdf_url.json` are empty
* Add `--debug` option. If you see `HTTP 429 Too Many Requests` error, it is because Google has banned our requests (see [how it works](#how-it-works) for details). The solution is: <a name="cookie"></a>
    * Use whatever explorer you like; install an extension which can export your cookies; login your Google account; open Google scholar and search something; export your cookies to `./cookies.txt`, make sure to remove all `#HttpOnly_` in this file if any.
    * When running the tool, specify `--user_agent` option as the user agent your explorer is using. For example,
` --user_agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:56.0) Gecko/20100101 Firefox/56.0"`
    * Every time 429 error happens, use the explorer to search something on Google Scholar, then a captcha should pop up. Clean it and then re-export the `cookies.txt` again. In our tests, usually after processing 50~100 papers this error will happen.
    * You may want to specify `--fix_pdf_url` option. This option will keep the PDF URLs you already have, and query only the missing ones. Alternatively, you can delete `<>.pdf_url.json`, and the tool we fetch URL for all papers.

* The other possibility is that the title is wrong. In many cases, it is because the author has changed the paper title after camera ready, but the website still displays their old names. For these cases, you can just correct the paper titles in `<>.paper_list.json`, delete `<>.pdf_url.json`, and run the tool again.

### Help message
You can always use
```
python pd.py --help
```
to learn about all options and functions.

## How it works
### Detecting paper titles
HTML is basically a tree structure with each node in charge of a block in UI. As a reasonable way of writing the webpage, the paper titles should present in the same level of the tree, and the node types of their ancestors should have the same pattern. Therefore, the tool will group all text nodes according to their path to the root. For each group of texts, the tool uses some simple heuristics (e.g., number of words) to determine if the group is titles. The heuristics we use are very simple, but they turn out to work well in our (limited) tests.

By default, the path to the root only considers the node type (e.g., div, ul, strong). In some cases, titles happen to have the same node type path with some other random strings. In these cases, you can include other node properties (e.g., class) into the path discrimination, using `-a` option.
 
### Getting PDF links
After getting the list of paper titles, the tool will search them over Google Scholar to get the PDF links. This part is based on a fantastic [Google Scholar library](https://github.com/ckreibich/scholar.py), written by Christian Kreibich and other contributors. Many thanks!

## Contributing
### Contributing the PDF link results
As mentioned above, getting the correct JSON files might require some manual efforts. If you successfully getting the PDF links using this tool, we encourage you to make a pull request to upload the JSON files (`<>.pdf_url.json`, `<>.paper_list.json`, `<>.conf_url.json`) to this repo. 
> To keep it consistent, please make the conference name to be all lower cases + 4 digit year, for example, `nsdi2019.pdf_url.json`, `nsdi2019.paper_list.json`, and `nsdi2019.conf_url.json`.

After having these files, other users can easily download or merge the papers.

### Contributing to the tool
If you find bugs/problems/suggestions or want to add more features to this library, feel free to submit issues or make pull requests.

