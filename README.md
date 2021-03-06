# index_generator


This is the result of my final project for the AllWomen Data Science bootcamp. The aim of this project was to explore whether it is possible to automatically generate the analytic index (sometimes called "back-of-the-book index") of an academic book.

Analytic indexes are typically found at the end of books and contain an alphabetized list of important concepts/names found in the book with references of the pages where they can be found. They also contain some information about relations of similarity between different keywords as well as lists of secondary keywords (deriving from a main keyword).


<p align="center">
<img src="./doc/elements.jpg" alt="drawing" width="700"/>
 <br>
    <em>The main elements of an index</em>
</p>



These indexes are present in practically all academic books and they make their reading much easier while also providing a very exhaustive overview of their contents. Their development is, nevertheless, very time consuming and a rather tedious task (I know this first hand, since some years ago I was asked to make one for [this book](https://link.springer.com/book/10.1057/9781137472519)), so it seems like it would be a good thing to automatize it.


<p align="center">
<img src="./doc/Novus_Atlas_Sinensis_-_First_page_of_the_index.jpg" alt="drawing" width="500"/>
 <br>
    <em>We've been using analytic indexes for a long time. The first one known to us dates back to the 16th century. This one is the index of Novus Atlas Sinensis by Martino Martini (1655)</em>
</p>

From the point of view of NLP, this is a keyword extraction problem. My approach was to treat it as a supervised binary classification task.

The idea was to create a dataset of candidate keywords, extract linguistic features from them (in some cases, relative to their context -- i.e. book, section, sentence), and try to predict whether they were supposed to go into the index based on these.

## Pipeline

My starting point were 22 books in pdf (all including an analytic index). Their topics were varied, but they were predominantly about philosophy and linguistics (these were simply the books I had available).

![Pipeline](./doc/pipeline.jpg "Pipeline")

## The final dataset

857000 candidate keywords / 10 linguistic features

The candidate keywords consisted of unigrams and bigrams (if I go beyond that, my personal computer cannot handle the size of the dataset!) extracted after a relatively moderate cleaning process. The reason why the cleaning can not be too aggresive is that we risk missing out on potential index keywords.

The main part of my project was the extraction of the linguistic features. Some of them are simply motivated by an intuition on my part of what could be significant for appearing in an index (in part based on my own experience as an indexer). But a few of them I adopted from similar works (see Wu et al [2013], Koutropolou and Galloupoulos [2019]).

List of features:

- Part of speech
- Position in sentence
- Absolute frequency
- Does it appear in a section title?
- Does it appear as an author in the bibliography?
- Tf-Idf scores relative to the deepest available section nesting
- Importance: Cosine similarity between the sentence embedding and the whole book's embedding
- Length of the word
- Is it a typical textbook word?
- Is it a named entity?

Target variable: Is it in the index?

## A general model

My best model was an XGBoost classifier. And my resulting metrics were:

| Metric| Value|
| ------------- |:-------------:|
| Accuracy| 0.99|
| Precision| 0.72 |
| Recall| 0.23|
| F1| 0.35|

Since the task we're dealing with is one in which we need to identify rare events (in this case, being in the index is rare), the dataset is extremely imbalanced wrt the target variable. Thus, accuracy is irrelevant for us: the model is very accurate, because it almost always predicts keywords to not be in the index. What we care about is precision (how exact the model is) and recall (how complete it is). In this case, we are doing fairly ok with precision, but not that well with recall. This means that many (72%) of the words classified as being in the index are indeed in the index, but that we are only catching 23% of the words in the index as being there.

Here's a representation of feature importance for this model (based on SHAP values):
<p align="center">
<img src="./doc/shap_beeswarm_xgb1.png" alt="drawing" width="500"/>
</p>
<!-- Update with better plot and comment -->

It's good to see some of my intuitions confirmed, like that being a named entity or being a named author are decisive for being in the index. It's also nice to see confirmed that the later a word appears in a sentence the more likely it is that it is in the index. I also find interesting that frequency has such a big impact on the predictions. I did not expect it to be that blatant. Another interesting result concerns the feature I call "importance". I would have thought that the more important its context is, the more likely it is that the word is in the index, but apparently it's the opposite. This is one of the things that I'd like to understand better in the future. My guess is that my way of calculating importance via sentence embeddings and cosine similarity is somehow problematic or just does not capture what I think it's capturing.

Training the model with oversampling (SMOTE) gave a much better recall (with a trade-off on precision, of course). This may be preferable if the resulting index is to serve a human indexer as a tool from which to extract the actual final index, since it means that many more words that are actually in the index are being identified as such by my model (and I assume that, for a human indexer, it'd be easier to remove keywords than to add them). 

| Metric| Value|
| ------------- |:-------------:|
|Accuracy| 0.97|
|Precision | 0.19|
|Recall | 0.62|
|F1 | 0.30|

However, this is only at the expense of introducing made up observations into our dataset as well as of higher computational costs.

Overall, I am relatively satisfied with these results. Firstly, as far as I can tell, they are comparable with the metrics gotten by other attempts to automatize index generation, which tells me I'm not completely off track. More generally, it was to be expected that this task would be difficult to fully automatize. After all, it is a job that's difficult for us, humans, in the first place. To quote the Chicago Manual of Style:

>The ideal indexer sees the work as a whole, understands the emphasis of the various parts and their relation to the whole, and knows what readers of the particular work are likely to look for. The indexer should be widely read, scrupulous in handling detail, analytically minded and well acquainted with publishing practices.

It seems a lot to ask of an ML model. 

On top of the task being complex, it is highly subjective. It is done by different people with different criteria. There are no strict standards or methods to produce an index. And, on top of that, the criteria change between different fields. For example: technical books tend to omit author names, while humanities books tend to include them.

This final observation led me to consider the hypothesis that specialized models for different academic fields would do better than general models, like the one I trained.

## A specialized model for philosophy books

To test this hypothesis (admittedly, to a rather limited extent), I trained a model on a subset of the original set of books, consisting of 10 philosophy books.

The results were indeed considerably better on all counts (bear in mind that these are the results without applying SMOTE):

| Metric| Value|
| ------------- |:-------------:|
|Accuracy| 0.99|
|Precision | 0.78|
|Recall | 0.37|
|F1 | 0.59|



<p align="center">
<img src="./doc/comp_metrics.jpg" alt="drawing" width="400"/>
<br>
    <em>A comparison of the metrics of both models</em>
</p>

## Final remarks

My tentative conclusion is that analytic indexes cannot be automatically generated just yet. However, we can build pretty good draft indexes to help human indexers.

This work was done rather hastily, over a period of 6 weeks, so there are plenty of things to improve. If I had more time, I would work on the following:

- Go beyond extractive method: some of the words in analytic indexes are not actually present in the body of books, but are generated by the indexer.
- Train model on bigger and more balanced dataset (i.e. balanced wrt the types of books included).
- Include trigrams as candidate keywords.
- Improve cleaning pipeline.
- Work on finding another way of capturing the importance of contexts as a linguitic feature (less computationally costly and more effective).
- Work on the processing of formalism from pdf to txt, since most mathematical symbols are lost in my implementation.




<p align="center">
<img src="./doc/my_index.png" alt="drawing" width="600"/>
<br>
    <em> A capture of one of the indexes generated by my programme </em>
</p>


## References

Koutropolou and Galloupoulos (2019) *TMG-BoBI: Generating Back-of-the-Book Indexes with the Text-to-Matrix Generator*. 10th International Conference on Information, Intelligence, Systems and Applications (IISA), pp. 1-8.

Wu et al (2013) *Can back-of-the-book indexes be automatically created?*. CIKM '13: Proceedings of the 22nd ACM international conference on Information & Knowledge Management, pp. 1745???1750.




