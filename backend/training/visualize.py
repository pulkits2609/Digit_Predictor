from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def save_figures(out: Path, images, labels, history, matrix):
    fig, axes = plt.subplots(2, 5, figsize=(9,4))
    for i, ax in enumerate(axes.flat):
        ax.imshow(images[i],cmap="gray")
        ax.set_title(f"Label: {labels[i]}")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out/"samples.png",dpi=150)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax, metric in zip(axes,["accuracy","loss"]):
        ax.plot(range(1,len(history[metric])+1), history[metric],label="Training")
        ax.plot(range(1,len(history[metric])+1), history[f"val_{metric}"],label="Validation")
        ax.set(xlabel="Epoch",ylabel=metric.capitalize())
        ax.legend()
    fig.tight_layout()
    fig.savefig(out/"training-curves.png",dpi=150)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,5))
    heat=ax.imshow(matrix,cmap="Blues")
    ax.set(xlabel="Predicted digit",ylabel="True digit",xticks=range(10),yticks=range(10))
    for y in range(10):
        for x in range(10):
            ax.text(x,y,str(matrix[y][x]),ha="center",va="center",fontsize=7,color="white" if matrix[y][x]>500 else "black")
    fig.colorbar(heat,ax=ax)
    fig.tight_layout()
    fig.savefig(out/"confusion-matrix.png",dpi=150)
    plt.close(fig)
