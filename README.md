Vanyad
======

A Nagios/Icinga helper for large network installations (>1000 nodes, thousands of services).
The objective is to create an entity responsible for a large number of purely mechanical tasks,
usually made by tech-support personel, which are needed to attain a situational picture of the network.
Under a large network it is hard to rely on the human factor to do this. Besides, reporting and fancy graphical
interfaces became quite a problem for real-time activities as they don't have the quality and capacity 
to deliver the precise information to the those who need it. Generically, these interfaces are 
only useful for post-factum analysis (aka "when all the milk is split").

Vanyad does not pretend to substitute the standard warning/command interfaces on Nagios/Icinga. 
In fact it uses them mostly as a user. In some ways, vanyad is a user like anyone else.

Right now, it is on a stage of early development, but most part of the code works pretty well.
It is mostly made under the working conditions of a specific network. While there are attempts
to abstract the code from the real environment, still, most algorithms are still bounded to particular 
conditions. So, tweaking will be needed if one wishes to use it on other networks.

It uses Livestatus and gets a little help from Prolog, but don't think this is AI on the rocks. 
Prolog is here just as a great tool for graph manipulation.  

