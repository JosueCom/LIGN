from .train import norm_labels
from .utils import clustering as cl
import torch as th
from .utils import io
import matplotlib.pyplot as plt


def validate(model, graph, train, tag_in, tag_out, labels, metrics=['accuracy'], sv_img=None, cluster=(cl.NN(), 3), device=th.device('cpu')):

    model.eval()
    with th.no_grad():
        # get k (cluster[1]) nodes's indexes from each label for clustering
        tr_nodes, tr_labs = cl.filter_k(tag_out, labels, train, cluster[1])
        # isolate nodes from parent
        sub = train.subgraph(tr_nodes)
        # get nodes feature input
        inp = sub.get_parent_data(tag_in).to(device)

        cluster = cluster[0]
        # train clustering
        cluster.train(model(sub, inp), tr_labs.to(device))

        # get all nodes with the labels that we are training
        ts_nodes = cl.filter(tag_out, labels, graph)
        # isolate those nodes from parents
        graph = graph.subgraph(ts_nodes)

        # get all apporpitae nodes input data
        inp = graph.get_parent_data(tag_in).to(device)
        # get all apporpitae nodes input data
        outp_t = graph.get_parent_data(tag_out).to(device)

        rep_vec = model(graph, inp)
        outp_p = cluster(rep_vec)

    if sv_img:  # save 2d image

        fig = plt.figure()
        tp = rep_vec.cpu().detach().numpy()
        tp2 = outp_t.cpu().detach().numpy()

        if sv_img[0] == '3d':
            ax = fig.add_subplot(111, projection='3d')

            c = ax.scatter(tp[:, 0], tp[:, 1], tp[:, 2], c=tp2, cmap=plt.get_cmap(
                'gist_rainbow'), vmin=0, vmax=sv_img[1])

        else:  # save 3d image
            c = plt.scatter(tp[:, 0], tp[:, 1], c=tp2, cmap=plt.get_cmap(
                'gist_rainbow'), vmin=0, vmax=sv_img[1])
            # plt.ylim([-1.2,1.2])
            # plt.xlim([-1.2,1.2])

        plt.colorbar(c).set_label("Label")
        plt.savefig("data/views/Validate "+str(len(labels))+".png")
        plt.close()

    out = {}
    metrics = io.to_iter(metrics)
    for metric in metrics:
        if metric == 'accuracy':
            out[metric] = (outp_p == outp_t).sum().item() * \
                100.0/outp_p.size(0)

    return out


def accuracy(model, graph, train, tag_in, tag_out, labels, cluster=(cl.NN(), 3), sv_img=None, device=th.device('cpu')):

    out = validate(model, graph, train, tag_in, tag_out, labels,
                   metrics='accuracy', cluster=cluster, sv_img=sv_img, device=device)

    return out['accuracy']
